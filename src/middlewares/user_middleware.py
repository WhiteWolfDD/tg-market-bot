from aiogram import BaseMiddleware
from aiogram.types import Update
import asyncio
from src.utils.cache import get_or_create_user


class UserMiddleware(BaseMiddleware):
    """
    Middleware for user.
    """

    async def __call__(self, handler, event, data):
        user_id = None

        # Extract the relevant part of the Update
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                user_id = event.message.from_user.id
            elif event.callback_query and event.callback_query.from_user:
                user_id = event.callback_query.from_user.id

        if user_id:
            # Run user retrieval in parallel with the handler
            get_user_task = asyncio.create_task(get_or_create_user(user_id, event))
            result = await handler(event, data)
            await get_user_task
            return result

        return await handler(event, data)