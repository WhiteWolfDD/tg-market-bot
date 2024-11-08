import json
from typing import Optional

from redis import asyncio as aioredis
from sqlalchemy import select

from src.database import get_session
from src.models.user import User
from src.utils.redis import get_redis


class UserService:
    """
    User service.
    """

    @staticmethod
    async def get_or_create_user(user_id, event):
        redis_client = await get_redis()
        try:
            user_data = await redis_client.get(f"user:{user_id}")
        except aioredis.TimeoutError:
            user_data = None

        if user_data:
            return User(**json.loads(user_data))

        # If not found in cache, query database
        async with get_session() as session:
            result = await session.execute(select(User).where(User.telegram_user_id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                user = User(
                    telegram_user_id=user_id,
                    language=event.from_user.language_code or 'en',
                    username=event.from_user.username or None
                )
                session.add(user)
                await session.commit()

            # Cache user data
            await redis_client.set(f"user:{user_id}", json.dumps(user.to_dict()), ex=3600)

        return user

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
