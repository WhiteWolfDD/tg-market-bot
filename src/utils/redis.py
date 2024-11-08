import os
from dotenv import load_dotenv

from redis import asyncio as aioredis

from src.utils.singleton import SingletonMeta

load_dotenv()


class RedisCache(metaclass=SingletonMeta):
    def __init__(self):
        self._client = aioredis.from_url(
            os.getenv("REDIS_URL"),
            password=os.getenv("REDIS_PASSWORD")
        )

    async def get_client(self):
        return self._client


async def get_redis() -> aioredis.Redis:
    redis_cache = RedisCache()
    return await redis_cache.get_client()
