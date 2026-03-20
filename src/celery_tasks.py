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
    всинхронная задача для субструктурного поиска
    args:
        substructure_smiles: SMILES субструктуры для поиска
    returns:
        результаты поиска
    """
    logger.info(f"начало задачи поиска: {substructure_smiles}")

    db: Session = SessionLocal()
    try:
        # обновляем статус задачи
        self.update_state(state="PROGRESS", meta={"current": 0, "total": 100})

        # получаем данные из бд
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

        all_molecules = db_manager.get_all_molecules(skip=0, limit=total_molecules)
        smiles_list = [mol.smiles for mol in all_molecules]

        self.update_state(state="PROGRESS", meta={"current": 30, "total": 100})

        found_smiles = substructure_search(smiles_list, substructure_smiles)

        self.update_state(
            state="PROGRESS",
            meta={"current": 80, "total": 100, "found_count": len(found_smiles)},
        )

        results = [
            {"id": mol.id, "smiles": mol.smiles, "name": mol.name} for mol in all_molecules if mol.smiles in found_smiles
        ]

        logger.info(f"готово: найдено {len(results)} молекул")

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
    тестовая задача для проверки работы Celery
    args:
        duration: секунды
    """
    logger.info(f"начало тестовой задачи на {duration} секунд")

    for i in range(duration):
        time.sleep(1)
        current_task.update_state(
            state="PROGRESS", meta={"current": i + 1, "total": duration}
        )

    return {"message": f"выполнено за {duration} секунд", "result": "success"}


@celery_app.task(name="cleanup_old_tasks")
def cleanup_old_tasks():
    """
    очистка старых результатов задач (запускается периодически)
    """
    return {"cleaned": True}
