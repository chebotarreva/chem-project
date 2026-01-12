"""
Celery задачи для химического поиска
"""

import logging
import time

from celery import current_task
from sqlalchemy.orm import Session

from src.api.database import DatabaseManager
from src.celery_app import celery_app
from src.db.session import SessionLocal
from src.main import substructure_search

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="substructure_search_task")
def substructure_search_task(self, substructure_smiles: str):
    """
    Асинхронная задача для субструктурного поиска

    Args:
        substructure_smiles: SMILES субструктуры для поиска

    Returns:
        Результаты поиска
    """
    logger.info(f"Начало задачи поиска: {substructure_smiles}")

    db: Session = SessionLocal()
    try:
        # 1. Обновляем статус задачи
        self.update_state(state="PROGRESS", meta={"current": 0, "total": 100, "status": "Подготовка к поиску..."})

        # 2. Получаем данные из БД
        db_manager = DatabaseManager(db)
        total_molecules = db_manager.count_molecules()

        self.update_state(
            state="PROGRESS",
            meta={
                "current": 10,
                "total": 100,
                "status": f"Загружено {total_molecules} молекул",
                "total_molecules": total_molecules,
            },
        )

        # 3. Получаем все SMILES
        all_molecules = db_manager.get_all_molecules(skip=0, limit=total_molecules)
        smiles_list = [mol.smiles for mol in all_molecules]

        # 4. Выполняем поиск
        self.update_state(state="PROGRESS", meta={"current": 30, "total": 100, "status": "Выполнение химического поиска..."})

        found_smiles = substructure_search(smiles_list, substructure_smiles)

        # 5. Формируем результаты
        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "status": "Формирование результатов...", "found_count": len(found_smiles)},
        )

        results = [
            {"id": mol.id, "smiles": mol.smiles, "name": mol.name} for mol in all_molecules if mol.smiles in found_smiles
        ]

        # 6. Возвращаем результат
        logger.info(f"Задача завершена: найдено {len(results)} молекул")

        return {
            "substructure": substructure_smiles,
            "found_count": len(results),
            "results": results,
            "task_id": current_task.request.id,
            "total_processed": total_molecules,
        }

    except Exception as e:
        logger.error(f"ОШИБКА в задаче поиска: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="test_task")
def test_task(duration: int = 5):
    """
    Тестовая задача для проверки работы Celery

    Args:
        duration: Длительность выполнения (секунды)
    """
    logger.info(f"Начало тестовой задачи на {duration} секунд")

    for i in range(duration):
        time.sleep(1)
        current_task.update_state(
            state="PROGRESS", meta={"current": i + 1, "total": duration, "status": f"Обработка... {i + 1}/{duration}"}
        )

    return {"message": f"Задача выполнена за {duration} секунд", "result": "success"}


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks():
    """
    Очистка старых результатов задач (запускается периодически)
    """
    # Здесь можно добавить очистку старых записей в Redis
    logger.info("Запущена очистка старых задач")
    return {"cleaned": True}
