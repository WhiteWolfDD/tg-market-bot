import json
from typing import List, Dict, Any

from redis import asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload

from src.database import get_session
from src.models import Category, CategoryTranslation
from src.utils.log import setup_logging
from src.utils.redis import get_redis

logger = setup_logging()

class CategoryService:
    """
    Category services.
    """

    @staticmethod
    async def get_category_by_id(category_id: int):
        redis_client = await get_redis()
        try:
            category = await redis_client.get(f"category:{category_id}")
        except aioredis.TimeoutError:
            category = None

        if category:
            return json.loads(category)

        async with get_session() as session:
            result = await session.execute(
                select(Category).options(
                    joinedload(Category.translations),
                    joinedload(Category.advertisements)
                ).where(Category.id == category_id)
            )
            category = result.unique().scalar_one_or_none()

            if category:
                category_dict = {
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

                await redis_client.set(f"category:{category_id}", json.dumps(category_dict), ex=3600)
                return category_dict

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
    async def toggle_category_and_children_status(category_id: int) -> None:
        """
        Toggle the status of a category and its children, and update the cache accordingly.

        :param category_id: The ID of the category.
        """
        async with get_session() as session:
            result = await session.execute(
                select(Category.path, Category.status)
                .where(Category.id == category_id)
            )
            category = result.first()
            if not category:
                logger.warning(f"Category with ID {category_id} not found.")
                return

            current_path, current_status = category
            new_status = not current_status

            logger.debug(f"Toggling status for categories with path like '{current_path}%' to {new_status}.")

            # Update the status of the category and its children
            await session.execute(
                update(Category)
                .where(Category.path.like(f"{current_path}%"))
                .values(status=new_status)
            )
            await session.commit()

        await CategoryService.update_cache_for_path(current_path, new_status)

    @staticmethod
    async def update_cache_for_path(path_prefix: str, new_status: bool) -> None:
        """
        Update the status of categories in the cache that match the given path prefix.

        :param path_prefix: The path prefix of the categories whose status should be updated.
        :param new_status: The new status to assign.
        """
        redis_client = await get_redis()

        cached_categories_json = await redis_client.get("categories")
        if not cached_categories_json:
            logger.warning("Cache 'categories' is empty. Skipping cache update.")
            return

        categories = json.loads(cached_categories_json)

        updated = False
        for category in categories:
            if category['path'].startswith(path_prefix):
                if category['status'] != new_status:
                    logger.debug(f"Updating status for category ID {category['id']} from {category['status']} to {new_status}.")
                    category['status'] = new_status
                    updated = True

        if updated:
            await redis_client.set("categories", json.dumps(categories), ex=3600)
            await redis_client.publish("categories", "update")
            logger.info("Cache 'categories' updated successfully.")
        else:
            logger.info("No categories needed status updates in cache.")

    @staticmethod
    async def get_categories_from_cache() -> List[Dict[str, Any]]:
        """
        Get categories from Redis cache.

        :return: List of categories.
        """
        redis_client = await get_redis()
        cached_categories_json = await redis_client.get("categories")
        if cached_categories_json:
            return json.loads(cached_categories_json)
        else:
            logger.warning("Cache 'categories' is empty. Fetching from DB.")
            return await CategoryService.get_categories_from_db()

    @staticmethod
    async def get_categories_from_db() -> List[Dict[str, Any]]:
        """
        Get all categories from the database and update the cache.

        :return: List of categories.
        """
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

        await CategoryService.set_categories(category_dicts)

        return category_dicts

    @staticmethod
    async def set_categories(categories: List[Dict[str, Any]], update_status_only: bool = False) -> None:
        """
        Invalidate the cache for categories and set the new categories.

        :param categories: List of categories.
        :param update_status_only: Flag indicating whether to update only the status.
        """
        redis_client = await get_redis()

        if update_status_only:
            cached_categories_json = await redis_client.get("categories")
            if not cached_categories_json:
                logger.warning("Cache 'categories' is empty. Skipping partial cache update.")
                return

            cached_categories = json.loads(cached_categories_json)

            updated = False
            for updated_category in categories:
                for category in cached_categories:
                    if category['id'] == updated_category['id']:
                        if category['status'] != updated_category['status']:
                            logger.debug(f"Updating status for category ID {category['id']} from {category['status']} to {updated_category['status']}.")
                            category['status'] = updated_category['status']
                            updated = True
                        break

            if updated:
                await redis_client.set("categories", json.dumps(cached_categories), ex=3600)
                logger.info("Partial cache 'categories' updated successfully.")
            else:
                logger.info("No categories needed status updates in partial cache.")

            return

        await redis_client.set("categories", json.dumps(categories), ex=3600)
        logger.info("Cache 'categories' set successfully.")