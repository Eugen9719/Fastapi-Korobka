import json
from typing import Optional

import redis.asyncio as redis
import sentry_sdk

from backend.app.services.serialize import serialize_datetime, deserialize_datetime
import logging

# Настройка логирования
logger = logging.getLogger(__name__)


class RedisClient:
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None

    async def connect(self):
        self.redis = redis.Redis.from_url(self.redis_url, decode_responses=True)

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def get_client(self):
        if not self.redis:
            await self.connect()
        return self.redis

    async def cache_data(self, cache_key: str, data: dict, expire_time: int = 600) -> None:
        """
        Кеширует данные в Redis.
        :param cache_key: Ключ для кеширования.
        :param data: Данные для кеширования.
        :param expire_time: Время жизни кеша в секундах.
        """
        try:
            client_redis = await self.get_client()
            await client_redis.setex(cache_key, expire_time, json.dumps(data, default=serialize_datetime))
        except Exception as e:
            logger.error(f"Error caching data: {e}")

    async def fetch_cached_data(self, cache_key: str, schema) -> Optional[dict]:
        """
        Получает данные из кеша.
        :param cache_key: Ключ для получения данных.
        :param schema: Схема для десериализации данных.
        :return: Десериализованные данные или None, если данных нет в кеше.
        """
        try:
            client_redis = await self.get_client()
            cached_data = await client_redis.get(cache_key)
            if cached_data:
                cached_data = json.loads(cached_data)
                cached_data = deserialize_datetime(cached_data)
                cached_data["items"] = [schema(**item) for item in cached_data["items"]]
                return cached_data
            return None
        except Exception as e:
            logger.error(f"Ошибка получения данных из кеша : {e}")
            return None

    async def delete_cache_by_prefix(self, prefix: str) -> None:
        """
        Удаляет все ключи из кеша с префикса.
        :param prefix: Префикс для поиска ключей.
        """
        try:
            client_redis = await self.get_client()
            cursor = "0"
            while cursor != 0:
                # Используем SCAN для поиска ключей по префиксу
                cursor, keys = await client_redis.scan(cursor=cursor, match=f"{prefix}*")
                if keys:
                    # Удаляем найденные ключи
                    await client_redis.delete(*keys)
        except Exception as e:
            logger.error(f"ошибка удаления кеша по префиксу {prefix}: {e}")

    async def invalidate_cache(self, cache_key: str, message: str) -> bool:
        """
        Инвалидирует кеш и логирует операцию.

        :param cache_key: Ключ кеша для инвалидации.
        :param message: Сообщение для логирования.
        :return: True, если кеш успешно инвалидирован, иначе False.
        """
        try:
            await self.delete_cache_by_prefix(cache_key)
            logger.info(f"Кеш {cache_key} инвалидирован: {message}")
            sentry_sdk.capture_message(f"Кеш {cache_key} инвалидирован: {message}", level="info")
            return True
        except Exception as e:
            logger.warning(f"Ошибка при инвалидации кеша {cache_key}: {e}")
            sentry_sdk.capture_exception(e)
            return False






