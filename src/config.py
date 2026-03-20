import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME = "Molecular Search API"
    VERSION = "1.0.0"

    # бд
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./chem_database.db")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_TTL = int(os.getenv("REDIS_TTL", 3600))  # 1 час по умолчанию

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    if DATABASE_URL.startswith("sqlite"):
        SQLALCHEMY_CONNECT_ARGS = {"check_same_thread": False}
    else:
        SQLALCHEMY_CONNECT_ARGS = {}


settings = Settings()
