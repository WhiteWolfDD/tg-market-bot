import os
import json
from typing import Optional
from sqlalchemy import select
from dotenv import load_dotenv
from sqlalchemy.orm import joinedload

from src.database import get_session
from src.models import User, Category, CategoryTranslation
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


async def get_categories(force_db=False):
    redis_client = await get_redis()
    if not force_db:
        try:
            categories = await redis_client.get("categories")
        except aioredis.TimeoutError:
            categories = None

        if categories:
            return json.loads(categories)

    async with get_session() as session:
        result = await session.execute(
            select(Category).options(
                joinedload(Category.translations),
                joinedload(Category.advertisements)
            )
        )
        categories = result.scalars().unique().all()

        category_dicts = [
            {
                'id': category.id,
                'emoji': category.emoji,
                'parent_id': category.parent_id,
                'status': category.status,
                'translations': [
                    {'language_code': trans.language_code, 'name': trans.name}
                    for trans in category.translations
                ]
            }
            for category in categories
        ]

        await redis_client.set("categories", json.dumps(category_dicts), ex=3600)

    return category_dicts


async def get_categories_from_db():
    async with get_session() as session:
        result = await session.execute(
            select(Category).options(
                joinedload(Category.translations),
                joinedload(Category.advertisements)
            )
        )
        categories = result.scalars().unique().all()

    category_dicts = [
        {
            'id': category.id,
            'emoji': category.emoji,
            'parent_id': category.parent_id,
            'status': category.status,
            'translations': [
                {'language_code': trans.language_code, 'name': trans.name}
                for trans in category.translations
            ]
        }
        for category in categories
    ]

    # Update Redis cache
    await set_categories(category_dicts)

    return category_dicts


async def set_categories(categories, update_status_only=False):
    redis_client = await get_redis()

    async with get_session() as session:
        try:
            for category in categories:
                result = await session.execute(select(Category).where(Category.id == category['id']))
                category_db = result.scalar_one_or_none()
                if category_db:
                    if update_status_only:
                        category_db.status = category['status']
                    else:
                        category_db.status = category['status']
                        category_db.emoji = category['emoji']
                        category_db.parent_id = category['parent_id']
                else:
                    category_db = Category(
                        id=category['id'],
                        emoji=category['emoji'],
                        parent_id=category['parent_id'],
                        status=category['status']
                    )
                    session.add(category_db)

                if not update_status_only:
                    for translation in category['translations']:
                        result = await session.execute(select(CategoryTranslation).where(
                            CategoryTranslation.category_id == category['id'],
                            CategoryTranslation.language_code == translation['language_code']
                        ))
                        translation_db = result.scalar_one_or_none()
                        if translation_db:
                            translation_db.name = translation['name']
                        else:
                            translation_db = CategoryTranslation(
                                category_id=category['id'],
                                language_code=translation['language_code'],
                                name=translation['name']
                            )
                            session.add(translation_db)

            await session.commit()
        except Exception as e:
            await session.rollback()
            print(f"Error updating categories: {e}")
            raise

        await redis_client.set("categories", json.dumps(categories), ex=3600)


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
