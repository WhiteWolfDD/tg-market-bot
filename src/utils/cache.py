import os
import json
from typing import Optional
from sqlalchemy import select
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

from src.database import get_session
from src.database.main import async_session
from src.models import User, Category
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


async def get_categories():
    redis_client = await get_redis()
    try:
        # Получаем данные из Redis
        categories = await redis_client.get("categories")
    except aioredis.TimeoutError:
        categories = None

    if categories:
        # Данные есть в Redis, возвращаем их
        return json.loads(categories)

    # Если данных в Redis нет, получаем их из базы данных
    async with get_session() as session:
        result = await session.execute(
            select(Category).options(
                joinedload(Category.translations),
                joinedload(Category.advertisements)
            )
        )
        categories = result.scalars().unique().all()

        # Преобразуем объекты ORM в словари
        category_dicts = [
            {
                'id': category.id,
                'emoji': category.emoji,
                'parent_id': category.parent_id,
                'translations': [
                    {'language_code': trans.language_code, 'name': trans.name}
                    for trans in category.translations
                ]
            }
            for category in categories
        ]

        # Кэшируем данные в Redis на 1 час (ex=3600)
        await redis_client.set("categories", json.dumps(category_dicts), ex=3600)

        return category_dicts  # Возвращаем данные в виде словарей


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