import hashlib
import json
import logging
import pickle
from functools import wraps
from typing import Any, Callable, Optional

import redis

from src.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Класс для работы с Redis кешем"""

    def __init__(self):
        self.client = redis.Redis.from_url(settings.REDIS_URL)
        self.is_connected = False
        self._connect()

    def _connect(self) -> None:
        """Подключение к Redis"""
        try:
            self.client.ping()
            self.is_connected = True
            logger.info("Redis подключен успешно")
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            self.is_connected = False

    def health_check(self) -> bool:
        """Проверка здоровья Redis"""
        try:
            # Явно преобразуем результат в bool
            return bool(self.client.ping())
        except Exception:
            return False

    def get(self, key: str) -> Optional[Any]:
        """Получить значение по ключу"""
        try:
            data = self.client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Ошибка получения из кеша: {e}")
        return None

    def setex(self, key: str, ttl: int, value: Any) -> bool:
        """Сохранить значение с TTL"""
        try:
            serialized = pickle.dumps(value)
            result = self.client.setex(key, ttl, serialized)
            return bool(result)
        except Exception as e:
            logger.error(f"Ошибка сохранения в Redis: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Удалить ключ"""
        try:
            result = self.client.delete(key)
            return bool(result)
        except Exception as e:
            logger.error(f"Ошибка удаления ключа: {e}")
            return False

    def keys(self, pattern: str = "*") -> list:
        """Получить список ключей по шаблону"""
        try:
            keys = self.client.keys(pattern)
            return [k.decode("utf-8") if isinstance(k, bytes) else k for k in keys]
        except Exception as e:
            logger.error(f"Ошибка получения ключей: {e}")
            return []


# Создаем глобальный экземпляр кеша
cache = RedisCache()


def invalidate_cache(pattern: str = "*") -> bool:
    """Инвалидация кеша по шаблону"""
    if not cache.is_connected:
        return False

    try:
        keys = cache.keys(pattern)
        if keys:
            cache.client.delete(*keys)
            logger.info(
                f"Инвалидирован кеш по шаблону: {pattern}, удалено ключей: {len(keys)}"
            )
        return True
    except Exception as e:
        logger.error(f"Ошибка инвалидации кеша: {e}")
        return False


def cached(ttl: int = 300, key_prefix: str = "") -> Callable:
    """Декоратор для кеширования результатов функций"""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not cache.is_connected:
                return func(*args, **kwargs)

            # Генерация ключа кеша
            key_parts = [key_prefix, func.__module__, func.__name__]

            # Сериализуем аргументы для ключа
            for arg in args:
                if hasattr(arg, "__dict__"):
                    key_parts.append(json.dumps(arg.__dict__, sort_keys=True))
                else:
                    key_parts.append(str(arg))

            for k, v in kwargs.items():
                key_parts.append(f"{k}={v}")

            cache_key = hashlib.md5(
                ":".join(str(p) for p in key_parts).encode()
            ).hexdigest()
            full_key = f"cache:{key_prefix}:{cache_key}"

            # Пробуем получить из кеша
            cached_value = cache.get(full_key)
            if cached_value is not None:
                logger.debug(f"Кеш найден для ключа: {full_key}")
                return cached_value

            # Выполняем функцию если нет в кеше
            result = func(*args, **kwargs)

            # Сохраняем в кеш
            cache.setex(full_key, ttl, result)
            logger.debug(f"Кеш сохранен для ключа: {full_key}")

            return result

        return wrapper

    return decorator
