import asyncio
import json
from datetime import datetime, timezone

from sqlalchemy import select, func

from src.database import get_session
from src.models import Advertisement, Statistic, Category, User, CategoryTranslation
from src.utils.log import setup_logging
from src.utils.redis import get_redis

logger = setup_logging()


class StatisticService:
    """
    Services for statistics.
    """

    @staticmethod
    async def get_total_users():
        redis_client = await get_redis()
        cached_stats = await redis_client.get("full_statistics")
        if cached_stats:
            return json.loads(cached_stats).get('total_users', 0)

        async with get_session() as session:
            result = await session.execute(select(func.count(User.id)))
            total_users = result.scalar()
            statistic = await session.get(Statistic, 1)
            if not statistic:
                statistic = Statistic(id=1, total_users=total_users)
                session.add(statistic)
            else:
                statistic.total_users = total_users
            await session.commit()

        await StatisticService.update_cache_field('total_users', total_users)
        return total_users

    @staticmethod
    async def get_new_users_today():
        redis_client = await get_redis()
        cached_stats = await redis_client.get("full_statistics")
        if cached_stats:
            cached_data = json.loads(cached_stats)
            if 'new_users_today' in cached_data:
                return cached_data['new_users_today']

        async with get_session() as session:
            result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= func.date_trunc('day', func.now()))
            )
            new_users_today = result.scalar()
            statistic = await session.get(Statistic, 1)
            if not statistic:
                statistic = Statistic(id=1, new_users_today=new_users_today)
                session.add(statistic)
            else:
                statistic.new_users_today = new_users_today
            await session.commit()

        await StatisticService.update_cache_field('new_users_today', new_users_today)
        return new_users_today

    @staticmethod
    async def reset_daily_new_users():
        async with get_session() as session:
            statistic = await session.get(Statistic, 1)
            if statistic:
                statistic.new_users_today = 0
                await session.commit()

    @staticmethod
    async def update_active_users():
        redis_client = await get_redis()
        now_timestamp = int(datetime.now(timezone.utc).timestamp())
        one_hour_ago_timestamp = now_timestamp - 3600
        one_day_ago_timestamp = now_timestamp - 86400

        user_activity = await redis_client.hgetall('user_last_activity')

        active_users_count = 0
        users_to_delete = []
        for user_id_str, last_activity_timestamp_str in user_activity.items():
            last_activity_timestamp = int(last_activity_timestamp_str)
            if last_activity_timestamp >= one_hour_ago_timestamp:
                active_users_count += 1
            if last_activity_timestamp < one_day_ago_timestamp:
                users_to_delete.append(user_id_str)

        if users_to_delete:
            await redis_client.hdel('user_last_activity', *users_to_delete)

        async with get_session() as session:
            statistic = await session.get(Statistic, 1)
            if not statistic:
                statistic = Statistic(id=1, active_users=active_users_count)
                session.add(statistic)
            else:
                statistic.active_users = active_users_count
            await session.commit()

        await StatisticService.update_cache_field('active_users', active_users_count)

    @staticmethod
    async def increment_total_advertisements():
        async with get_session() as session:
            statistic = await session.get(Statistic, 1)
            if not statistic:
                statistic = Statistic(id=1, total_advertisements=1)
                session.add(statistic)
            else:
                statistic.total_advertisements += 1
            await session.commit()

        await StatisticService.update_cache_field('total_advertisements', statistic.total_advertisements)

    @staticmethod
    async def update_active_advertisements():
        async with get_session() as session:
            result = await session.execute(
                select(func.count(Advertisement.id))
            )
            active_ads = result.scalar()
            statistic = await session.get(Statistic, 1)
            if statistic:
                statistic.active_advertisements = active_ads
                await session.commit()

        await StatisticService.update_cache_field('active_advertisements', active_ads)

    @staticmethod
    async def update_successful_advertisements():
        async with get_session() as session:
            result = await session.execute(
                select(func.count(Advertisement.id)).where(Advertisement.status == 'approved')
            )
            successful_ads = result.scalar()
            statistic = await session.get(Statistic, 1)
            if statistic:
                statistic.successful_advertisements = successful_ads
                await session.commit()

        await StatisticService.update_cache_field('successful_advertisements', successful_ads)

    @staticmethod
    async def update_deleted_advertisements():
        async with get_session() as session:
            statistic = await session.get(Statistic, 1)
            total_ads = statistic.total_advertisements if statistic else 0

            active_ads_result = await session.execute(
                select(func.count(Advertisement.id))
            )
            active_ads = active_ads_result.scalar()

            deleted_ads = total_ads - active_ads

            if statistic:
                statistic.deleted_advertisements = deleted_ads
                await session.commit()

        await StatisticService.update_cache_field('deleted_advertisements', deleted_ads)

    @staticmethod
    async def update_total_categories():
        async with get_session() as session:
            result = await session.execute(
                select(func.count(Category.id))
            )
            total_categories = result.scalar()
            statistic = await session.get(Statistic, 1)
            if statistic:
                statistic.total_categories = total_categories
                await session.commit()

        await StatisticService.update_cache_field('total_categories', total_categories)

    @staticmethod
    async def update_popular_categories():
        async with get_session() as session:
            result = await session.execute(
                select(
                    Category.id,
                    func.count(Advertisement.id).label('ad_count')
                )
                .join(Advertisement, Advertisement.category_id == Category.id)
                .group_by(Category.id)
                .order_by(func.count(Advertisement.id).desc())
                .limit(5)
            )
            popular_categories_data = result.all()

            category_ids = [row.id for row in popular_categories_data]
            categories = await session.execute(
                select(Category.id, Category.emoji, CategoryTranslation.name)
                .join(CategoryTranslation)
                .where(Category.id.in_(category_ids))
                .where(CategoryTranslation.language_code == 'en')
            )
            categories_dict = {cat.id: {'name': cat.name, 'emoji': cat.emoji} for cat in categories}

            popular_categories = []
            for row in popular_categories_data:
                category_info = categories_dict.get(row.id, {'name': 'Unknown', 'emoji': ''})
                popular_categories.append({
                    'category_id': row.id,
                    'category_name': category_info['name'],
                    'emoji': category_info['emoji'],
                    'ad_count': row.ad_count
                })

            statistic = await session.get(Statistic, 1)
            if statistic:
                statistic.popular_categories = popular_categories
                await session.commit()

        await StatisticService.update_cache_field('popular_categories', popular_categories)

    @staticmethod
    async def update_response_time_avg():
        """
        Calculate the average response time and store it in the statistics.
        """
        redis_client = await get_redis()
        try:
            response_times = await redis_client.lrange('response_times', 0, -1)
            if response_times:
                response_times = [float(rt) for rt in response_times]
                average_response_time = sum(response_times) / len(response_times)

                async with get_session() as session:
                    statistic = await session.get(Statistic, 1)
                    if not statistic:
                        statistic = Statistic(id=1, response_time_avg=average_response_time)
                        session.add(statistic)
                    else:
                        statistic.response_time_avg = average_response_time
                    await session.commit()

                await StatisticService.update_cache_field('response_time_avg', average_response_time)
                await redis_client.delete('response_times')
            else:
                logger.warning("No response times recorded.")
        except Exception as e:
            logger.error(f"Error updating average response time: {e}")

    @staticmethod
    async def get_full_statistics():
        redis_client = await get_redis()
        cached_stats = await redis_client.get("full_statistics")
        if cached_stats:
            return json.loads(cached_stats)

        async with get_session() as session:
            statistic = await session.get(Statistic, 1)
            if not statistic:
                return {}

            stats_dict = statistic.to_dict()

        await redis_client.set("full_statistics", json.dumps(stats_dict), ex=3600)

        return stats_dict

    @staticmethod
    async def reset_daily_statistics():
        await StatisticService.reset_daily_new_users()

    @staticmethod
    async def update_all_statistics():
        await asyncio.gather(
            StatisticService.get_total_users(),
            StatisticService.get_new_users_today(),
            StatisticService.update_active_users(),
            StatisticService.update_active_advertisements(),
            StatisticService.update_successful_advertisements(),
            StatisticService.update_deleted_advertisements(),
            StatisticService.update_total_categories(),
            StatisticService.update_popular_categories(),
            StatisticService.update_response_time_avg()
        )

        try:
            await StatisticService.reset_statistics_cache()
        except Exception as e:
            logger.error(f"Error resetting statistics cache: {e}")

    @staticmethod
    async def reset_statistics_cache():
        """
        Reset the statistics cache in Redis.
        """
        redis_client = await get_redis()
        await redis_client.delete("full_statistics")

    @staticmethod
    async def update_cache_field(field_name: str, value):
        """
        Update a specific field in the statistics cache.

        :param field_name: The name of the field to update.
        :param value: The new value of the field.
        """
        redis_client = await get_redis()
        cached_stats = await redis_client.get("full_statistics")
        if cached_stats:
            stats = json.loads(cached_stats)
            stats[field_name] = value
            await redis_client.set("full_statistics", json.dumps(stats), ex=3600)
        else:
            # If the cache is empty, update the field in the database and set it in the cache
            stats = {field_name: value}
            await redis_client.set("full_statistics", json.dumps(stats), ex=3600)
