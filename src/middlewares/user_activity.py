from aiogram import BaseMiddleware
from aiogram.types import Update
from datetime import datetime, timezone
from typing import Callable, Dict, Any

from src.utils.redis import get_redis
from src.utils.log import setup_logging

logger = setup_logging()


class UserActivityMiddleware(BaseMiddleware):
    """
    Middleware for updating user activity.
    """

    async def __call__(self, handler: Callable[[Update, Dict[str, Any]], Any], event: Update, data: Dict[str, Any]):
        user_id = None

        if event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id

        if user_id:
            try:
                await self.update_user_activity(user_id)
            except Exception as e:
                logger.error(f"Error updating user activity: {e}")

        return await handler(event, data)

    @staticmethod
    async def update_user_activity(user_id: int):
        """
        Update user last activity timestamp.
        """
        redis_client = await get_redis()
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        await redis_client.hset('user_last_activity', str(user_id), str(now_timestamp))
