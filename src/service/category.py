import json

from redis import asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database import get_session
from src.models import Category, CategoryTranslation
from src.utils.redis import get_redis


class CategoryService:
    """
    Category service.
    """

    @staticmethod
    async def get_category_by_id(category_id: int):
        async with get_session() as session:
            result = await session.execute(
                select(Category).options(
                    joinedload(Category.translations),
                    joinedload(Category.advertisements)
                ).where(Category.id == category_id)
            )
            category = result.unique().scalar_one_or_none()

            if category:
                return {
                    'id': category.id,
                    'emoji': category.emoji,
                    'parent_id': category.parent_id,
                    'status': category.status,
                    'path': category.path,
                    'translations': [
                        {'language_code': trans.language_code, 'name': trans.name}
                        for trans in category.translations
                    ]
                }

    @staticmethod
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
                    'path': category.path,
                    'translations': [
                        {'language_code': trans.language_code, 'name': trans.name}
                        for trans in category.translations
                    ]
                }
                for category in categories
            ]

            await redis_client.set("categories", json.dumps(category_dicts), ex=3600)

        return category_dicts

    @staticmethod
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
                'path': category.path,
                'translations': [
                    {'language_code': trans.language_code, 'name': trans.name}
                    for trans in category.translations
                ]
            }
            for category in categories
        ]

        # Update Redis cache
        await CategoryService.set_categories(category_dicts)

        return category_dicts

    @staticmethod
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
