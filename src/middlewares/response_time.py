from aiogram import BaseMiddleware
from aiogram.types import Update
from typing import Callable, Dict, Any
import time

from src.utils.redis import get_redis
from src.utils.log import setup_logging

logger = setup_logging()


class ResponseTimeMiddleware(BaseMiddleware):
    """
    Middleware for measuring and collecting response times.
    """

    async def __call__(self, handler: Callable[[Update, Dict[str, Any]], Any], event: Update, data: Dict[str, Any]):
        start_time = time.monotonic()
        try:
            return await handler(event, data)
        finally:
            end_time = time.monotonic()
            response_time = end_time - start_time
            # Store the response time
            await self.store_response_time(response_time)

    @staticmethod
    async def store_response_time(response_time: float):
        """
        Store the response time in Redis.
        """
        redis_client = await get_redis()
        try:
            # Store the response time in a list
            await redis_client.lpush('response_times', response_time)
            await redis_client.ltrim('response_times', 0, 999)  # Keep only the last 1000 response times
        except Exception as e:
            logger.error(f"Error storing response time: {e}")
