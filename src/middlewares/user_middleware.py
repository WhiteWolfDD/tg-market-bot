from aiogram import BaseMiddleware
from aiogram.types import Update
import asyncio
from src.services.user import UserService
from src.utils.log import setup_logging

logger = setup_logging()


class UserMiddleware(BaseMiddleware):
    """
    Middleware for user.
    """

    async def __call__(self, handler, event: Update, data: dict):
        user_id = None
        user_event = None

        # Extract the relevant part of the Update
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
                user_event = event.message
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id
                user_event = event.callback_query

        if user_id and user_event:
            try:
                get_user_task = asyncio.create_task(UserService.get_or_create_user(user_id, user_event))
                result = await handler(event, data)
                user = await get_user_task
                data['user'] = user
                return result
            except AttributeError as e:
                logger.error(f"UserMiddleware AttributeError: {e}")
                return await handler(event, data)
            except Exception as e:
                logger.exception(f"UserMiddleware unexpected error: {e}")
                return await handler(event, data)

        return await handler(event, data)