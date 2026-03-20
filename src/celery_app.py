"""
Конфигурация Celery для асинхронных задач
"""

from celery import Celery

from src.config import settings

celery_app = Celery(
    "chem_project",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    task_default_queue="default",
    task_routes={
        "substructure_search_task": {"queue": "search"},
    },
    broker_connection_timeout=30,
    broker_connection_retry=True,
    broker_connection_max_retries=3,
    result_backend_transport_options={"retry_policy": {"timeout": 5.0}},
    task_track_started=True,
    task_send_sent_event=True,
)

celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "src.celery_tasks.cleanup_old_tasks",
        "schedule": 3600.0,  # час
    },
}

if __name__ == "__main__":
    celery_app.start()
