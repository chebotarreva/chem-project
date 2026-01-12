# Универсальный импорт для SQLAlchemy 1.4 и 2.0
try:
    # Для SQLAlchemy 1.4+
    from sqlalchemy.orm import declarative_base
except ImportError:
    # Для старых версий SQLAlchemy (<1.4)
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()