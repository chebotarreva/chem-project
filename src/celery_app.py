"""
Конфигурация Celery для асинхронных задач
"""

from celery import Celery

from src.config import settings

# Создаем экземпляр Celery
celery_app = Celery(
    "chem_project",
    broker=settings.REDIS_URL,  # Redis как брокер сообщений
    backend=settings.REDIS_URL,  # Redis для хранения результатов
    include=["src.celery_tasks"],  # Файл с задачами
)

# Настройки Celery
celery_app.conf.update(
    # Базовые настройки
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    # Настройки производительности
    worker_prefetch_multiplier=1,  # По 1 задаче на worker
    task_acks_late=True,  # Подтверждение после выполнения
    worker_max_tasks_per_child=100,  # Перезапуск worker после 100 задач
    # Настройки очередей
    task_default_queue="default",
    task_routes={
        "substructure_search_task": {"queue": "search"},
    },
    # Время ожидания
    broker_connection_timeout=30,
    broker_connection_retry=True,
    broker_connection_max_retries=3,
    # Результаты
    result_backend_transport_options={"retry_policy": {"timeout": 5.0}},
    # Отслеживание прогресса
    task_track_started=True,
    task_send_sent_event=True,
)

# Опционально: можно добавить периодические задачи
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "src.celery_tasks.cleanup_old_tasks",
        "schedule": 3600.0,  # Каждый час
    },
}

if __name__ == "__main__":
    celery_app.start()
