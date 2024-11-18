import json
from typing import Optional, Union

from aiogram.types import Message, CallbackQuery
from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.orm import Mapped

from src.database import get_session
from src.models.user import User
from src.utils.log import setup_logging
from src.utils.redis import get_redis

logger = setup_logging()


class UserService:
    """
    User services.
    """

    @staticmethod
    async def get_or_create_user(user_id: int, event: Union[Message, CallbackQuery]) -> User:
        redis_client = await get_redis()
        try:
            user_data = await redis_client.get(f"user:{user_id}")
        except aioredis.TimeoutError:
            user_data = None

        if user_data:
            return User(**json.loads(user_data))

        if isinstance(event, Message):
            from_user = event.from_user
        elif isinstance(event, CallbackQuery):
            from_user = event.from_user
        else:
            logger.error("Unsupported event type for get_or_create_user.")
            raise AttributeError("'event' does not have 'from_user' attribute.")

        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_user_id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    telegram_user_id=user_id,
                    language=from_user.language_code or 'en',
                    username=from_user.username or None
                )
                session.add(user)
                await session.commit()

            await redis_client.set(
                f"user:{user_id}",
                json.dumps(user.to_dict()),
                ex=3600
            )

        return user

    @staticmethod
    async def get_user_id_by_telegram_id(telegram_user_id: int) -> Optional[int]:
        redis_client = await get_redis()
        try:
            user_id = await redis_client.get(f"telegram_user_id:{telegram_user_id}")
        except aioredis.TimeoutError:
            user_id = None

        if user_id:
            return int(user_id)

        async with get_session() as session:
            result = await session.execute(select(User.id).where(User.telegram_user_id == telegram_user_id))
            user_id = result.scalar_one_or_none()
            if user_id:
                await redis_client.set(f"telegram_user_id:{telegram_user_id}", user_id, ex=3600)
                return user_id
            else:
                return None

    @staticmethod
    async def get_user_telegram_id(user_id: Mapped[int] | int) -> Optional[int]:
        redis_client = await get_redis()
        try:
            telegram_user_id = await redis_client.get(f"user:{user_id}:telegram_id")
        except aioredis.TimeoutError:
            telegram_user_id = None

        if telegram_user_id:
            return int(telegram_user_id)

        async with get_session() as session:
            result = await session.execute(select(User.telegram_user_id).where(User.id == user_id))
            telegram_user_id = result.scalar_one_or_none()
            if telegram_user_id:
                await redis_client.set(f"user:{user_id}:telegram_id", telegram_user_id, ex=3600)
                return telegram_user_id
            else:
                return None

    @staticmethod
    async def get_user_locale(user_id: int) -> Optional[str]:
        redis_client = await get_redis()
        try:
            locale = await redis_client.get(f"user:{user_id}:language")
        except aioredis.TimeoutError:
            locale = None

        if locale:
            return locale.decode('utf-8')

        async with get_session() as session:
            result = await session.execute(select(User).where(User.telegram_user_id == user_id))
            user = result.scalar_one_or_none()
            if user:
                await redis_client.set(f"user:{user_id}:language", user.language, ex=3600)
                return user.language
            else:
                return None

    @staticmethod
    async def set_user_locale(user_id: int, locale: str):
        redis_client = await get_redis()
        try:
            await redis_client.set(f"user:{user_id}:language", locale, ex=3600)
        except aioredis.TimeoutError:
            pass

        try:
            async with get_session() as session:
                result = await session.execute(select(User).where(User.telegram_user_id == user_id))
                user = result.scalar_one_or_none()
                if user:
                    user.language = locale
                    await session.commit()
        except Exception as e:
            print(e)
            pass
