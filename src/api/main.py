import json
import logging
from datetime import datetime
from typing import Optional

from celery.result import AsyncResult
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.database import DatabaseManager
from src.api.models import MoleculeCreate, MoleculeResponse, MoleculesList, SearchRequest
from src.celery_app import celery_app
from src.celery_tasks import substructure_search_task, test_task
from src.config import settings
from src.db.session import get_db
from src.redis_cache import cache, invalidate_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME, description="API для хранения и поиска химических молекул", version=settings.VERSION
)

# --- вспомогательные функции для кеширования ---


def get_cache_key(substructure: str) -> str:
    """создает ключ для кеша на основе субструктуры"""
    return f"search:{substructure}"


async def get_cached_search(substructure: str):
    """получить результат поиска из кеша"""
    try:
        key = get_cache_key(substructure)
        cached = cache.get(key)
        if cached:
            logger.info(f"Найден кеш для {substructure}")
            result = json.loads(cached)
            result["cached"] = True
            return result
    except Exception as e:
        logger.warning(f"ОШИБКА чтения кеша: {e}")
    return None


async def save_to_cache(substructure: str, result: dict, ttl: int = 3600):
    """Сохранить результат поиска в кеш"""
    try:
        key = get_cache_key(substructure)
        # Сохраняем только нужные данные, без лишних объектов
        data_to_cache = {
            "substructure": result.get("substructure"),
            "found_count": result.get("found_count"),
            "results": [{"id": r.id, "smiles": r.smiles, "name": r.name} for r in result.get("results", [])],
            "search_type": result.get("search_type"),
        }
        cache.setex(key, ttl, json.dumps(data_to_cache))
        logger.info(f"Сохранен кеш для {substructure}")
    except Exception as e:
        logger.warning(f"ОШИБКА сохранения кеша: {e}")


# ==================== КОРНЕВОЙ ЭНДПОИНТ ====================


@app.get("/")
async def root():
    """корневой эндпоинт. информация об API"""
    return {
        "message": "Добро пожаловать в Chemical Molecules API!",
        "version": settings.VERSION,
        "documentation": "/docs",
        "health_check": "/health",
        "endpoints": {
            "api_docs": "/docs",
            "health": "/health",
            "search": "/search",
            "molecules": "/molecules/",
            "cache_stats": "/cache/stats",
            "async_tasks": "/tasks/search/async",
        },
    }


# ==================== CRUD ОПЕРАЦИИ ====================


@app.post(
    "/molecules/", response_model=MoleculeResponse, status_code=status.HTTP_201_CREATED,
    summary="Добавить новую молекулу"
)
async def create_molecule(molecule: MoleculeCreate, db: Session = Depends(get_db)):
    """добавить новую молекулу в БД"""
    from src.db.models import Molecule  # Явный импорт

    try:
        # Создаем SQLAlchemy объект без поля id
        db_molecule = Molecule(
            smiles=molecule.smiles,
            name=molecule.name
        )
        db.add(db_molecule)
        db.commit()
        db.refresh(db_molecule)
        logger.info(f"Создана молекула: id={db_molecule.id}, name={db_molecule.name}")

        invalidate_cache("search:*")

        return db_molecule
    except Exception as e:
        logger.error(f"ОШИБКА создания молекулы: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/molecules/{molecule_id}", response_model=MoleculeResponse, summary="Получить молекулу по ID")
async def read_molecule(molecule_id: int, db: Session = Depends(get_db)):
    """получить информацию о молекуле по её идентификатору"""
    db_manager = DatabaseManager(db)
    molecule = db_manager.get_molecule_by_id(molecule_id)

    if molecule is None:
        raise HTTPException(status_code=404, detail=f"ОШИБКА! Молекула с id={molecule_id} не найдена")

    return molecule


@app.put("/molecules/{molecule_id}", response_model=MoleculeResponse, summary="Обновить молекулу")
async def update_molecule(molecule_id: int, molecule: MoleculeCreate, db: Session = Depends(get_db)):
    """Обновить информацию о молекуле"""

    db_manager = DatabaseManager(db)
    updated = db_manager.update_molecule(molecule_id, molecule)

    if updated is None:
        raise HTTPException(status_code=404, detail=f"Молекула с id={molecule_id} не найдена")

    logger.info(f"Обновлена молекула: id={molecule_id}")
    invalidate_cache("search:*")
    return updated


@app.delete("/molecules/{molecule_id}", summary="Удалить молекулу")
async def delete_molecule(molecule_id: int, db: Session = Depends(get_db)):
    """удалить молекулу из БД"""
    db_manager = DatabaseManager(db)

    if db_manager.delete_molecule(molecule_id):
        logger.info(f"Удалена молекула: id={molecule_id}")

        invalidate_cache("search:*")

        return JSONResponse(status_code=200, content={"message": f"Молекула с id={molecule_id} удалена"})
    else:
        raise HTTPException(status_code=404, detail=f"Молекула с id={molecule_id} не найдена")


@app.get("/molecules/", response_model=MoleculesList, summary="Получить список молекул")
async def list_molecules(
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(10, ge=1, le=100, description="Размер страницы"),
    search: Optional[str] = Query(None, description="Поиск по названию или SMILES"),
    db: Session = Depends(get_db),
):
    """Получить список молекул с пагинацией"""
    db_manager = DatabaseManager(db)

    skip = (page - 1) * page_size

    molecules = db_manager.get_all_molecules(skip, page_size, search)
    total = db_manager.count_molecules()

    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return MoleculesList(molecules=molecules, total=total, page=page, page_size=page_size, total_pages=total_pages)


# ==================== СИНХРОННЫЙ ПОИСК ====================


@app.post("/search/")
async def search_substructure(request: SearchRequest, db: Session = Depends(get_db)):
    """Поиск молекул, содержащих заданную субструктуру (с простым кешированием)"""

    cached_result = await get_cached_search(request.substructure)
    if cached_result:
        return cached_result

    try:
        try:
            from src.main import substructure_search

            use_real_search = True
        except ImportError:
            logger.warning("Функция substructure_search не найдена, используется упрощенный поиск")
            use_real_search = False

        db_manager = DatabaseManager(db)

        # все SMILES из базы
        all_molecules = db_manager.get_all_molecules(skip=0, limit=db_manager.count_molecules())
        smiles_list = [mol.smiles for mol in all_molecules]

        if use_real_search:
            found_smiles = substructure_search(smiles_list, request.substructure)
        else:
            found_smiles = [smiles for smiles in smiles_list if request.substructure in smiles]

        results = [mol for mol in all_molecules if mol.smiles in found_smiles]

        logger.info(f"Выполнен поиск: субструктура={request.substructure}, найдено={len(results)}")

        result_data = {
            "substructure": request.substructure,
            "found_count": len(results),
            "results": results,
            "search_type": "real" if use_real_search else "simple",
            "cached": False,
        }

        await save_to_cache(request.substructure, result_data)

        return result_data

    except Exception as e:
        logger.error(f"ОШИБКА поиска: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"ОШИБКА при выполнении поиска: {str(e)}")


# ==================== CELERY ЗАДАЧИ ====================


@app.post("/tasks/search/async")
async def start_async_search(request: SearchRequest):
    """
    запуск асинхронного поиска по субструктуре
    """
    try:
        # запуск задачи сelery
        task = substructure_search_task.delay(request.substructure)

        logger.info(f"Запущена асинхронная задача поиска. Task ID: {task.id}")

        return {
            "message": "Поиск запущен в фоновом режиме",
            "task_id": task.id,
            "status": "PENDING",
            "check_status_url": f"/tasks/{task.id}/status",
            "get_results_url": f"/tasks/{task.id}/result",
        }

    except Exception as e:
        logger.error(f"ОШИБКА запуска задачи: {e}")
        raise HTTPException(status_code=500, detail=f"ОШИБКА запуска асинхронного поиска: {str(e)}")


@app.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """
    статус задачи
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        response = {
            "task_id": task_id,
            "status": task_result.status,
        }

        # если еще в процессе, отображается статус прогресса
        if task_result.status == "PROGRESS":
            response.update(task_result.info or {})
        elif task_result.status == "SUCCESS":
            response["ready"] = True
            response["result_available"] = True
        elif task_result.status == "FAILURE":
            response["error"] = str(task_result.info)

        return response

    except Exception as e:
        logger.error(f"Ошибка получения статуса задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"ОШИБКА получения статуса задачи: {str(e)}")


@app.get("/tasks/{task_id}/result")
async def get_task_result(task_id: str):
    """
    получение результата задачи (если готова)
    """
    try:
        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.status != "SUCCESS":
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Задача еще не завершена",
                    "task_id": task_id,
                    "status": task_result.status,
                    "check_status": f"/tasks/{task_id}/status",
                },
            )

        return {"task_id": task_id, "status": "SUCCESS", "result": task_result.result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ОШИБКА получения результата задачи {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"ОШИБКА получения результата задачи: {str(e)}")


@app.post("/tasks/test")
async def start_test_task(duration: int = Query(5, ge=1, le=60)):
    """
    Запуск тестовой задачи
    """
    try:
        task = test_task.delay(duration)

        return {
            "message": f"Тестовая задача запущена на {duration} секунд",
            "task_id": task.id,
            "status": "PENDING",
            "check_status_url": f"/tasks/{task.id}/status",
        }

    except Exception as e:
        logger.error(f"ОШИБКА запуска тестовой задачи: {e}")
        raise HTTPException(status_code=500, detail=f"ОШИБКА запуска тестовой задачи: {str(e)}")


@app.get("/tasks")
async def list_tasks(limit: int = Query(10, ge=1, le=100)):
    """
    Получение списка последних задач
    """
    try:
        return {
            "message": "Список задач пока недоступен",
            "note": "Для просмотра задач используйте Flower на порту 5555",
            "flower_url": "http://localhost:5555",
        }

    except Exception as e:
        logger.error(f"Ошибка получения списка задач: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка задач: {str(e)}")


# ==================== HEALTH & CACHE ====================


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Проверка здоровья API, базы данных, Redis и Celery"""
    from src.redis_cache import cache

    db_status = "unknown"
    redis_status = "unknown"
    celery_status = "unknown"

    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"disconnected: {str(e)}"

    redis_healthy = cache.health_check()
    redis_status = "connected" if redis_healthy else "disconnected"

    try:
        result = celery_app.control.ping(timeout=2)
        if result:
            celery_status = "connected"
        else:
            celery_status = "no_response"
    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        celery_status = f"disconnected: {str(e)}"

    overall_status = (
        "healthy"
        if all([db_status == "connected", redis_status == "connected", celery_status == "connected"])
        else "unhealthy"
    )

    return {
        "status": overall_status,
        "services": {"database": db_status, "redis": redis_status, "celery": celery_status},
        "version": settings.VERSION,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/cache/stats")
async def get_cache_stats():
    """Получить статистику кеша"""
    from src.redis_cache import cache

    if not cache.is_connected:
        raise HTTPException(status_code=503, detail="Redis недоступен")

    try:
        info = cache.client.info()
        return {
            "connected": True,
            "keys_count": cache.client.dbsize(),
            "used_memory": info.get("used_memory_human", "N/A"),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": (info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ОШИБКА получения статистики: {str(e)}")


@app.delete("/cache/clear")
async def clear_cache():
    """Очистить весь кеш"""
    from src.redis_cache import invalidate_cache

    success = invalidate_cache("*")

    if success:
        return {"message": "Кеш успешно очищен"}
    else:
        raise HTTPException(status_code=503, detail="Не удалось очистить кеш (Redis может быть недоступен)")


@app.delete("/cache/search")
async def clear_search_cache():
    """Очистить кеш поиска"""
    from src.redis_cache import invalidate_cache

    success = invalidate_cache("search:*")

    if success:
        return {"message": "Кеш поиска очищен"}
    else:
        raise HTTPException(status_code=503, detail="Не удалось очистить кеш поиска")


@app.get("/cache/test")
async def cache_test():
    """тест работы кеширования"""
    import time

    from src.redis_cache import cache, cached

    @cached(ttl=10, key_prefix="test")
    def slow_function(x):
        time.sleep(1)
        return {"result": x * 2, "timestamp": time.time()}

    start = time.time()
    result1 = slow_function(21)
    time1 = time.time() - start

    start = time.time()
    result2 = slow_function(21)
    time2 = time.time() - start

    return {
        "first_call_time": time1,
        "second_call_time": time2,
        "is_faster": time2 < time1,
        "same_result": result1 == result2,
        "redis_connected": cache.is_connected,
        "keys_in_cache": cache.client.dbsize() if cache.is_connected else 0,
    }
