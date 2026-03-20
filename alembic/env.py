import os
import sys

# абсолютный путь к корню проекта
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))

# добавляем project_root в путь Python
sys.path.insert(0, project_root)

try:
    from src.config import settings
    from src.db.base import Base
    print(f"ДА! Импорт успешен: {settings.DATABASE_URL}")
except ImportError as e:
    print(f"НЕТ! Ошибка импорта: {e}")
    # создаем Base здесь
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()