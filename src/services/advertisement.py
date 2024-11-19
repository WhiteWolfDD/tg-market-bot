import json

from sqlalchemy import select
from redis import asyncio as aioredis

from src.database import get_session
from src.models import MediaFile, UserAdvertisement
from src.models.advertisement import Advertisement
from src.utils.redis import get_redis


class AdvertisementService:
    """
    Advertisement services.
    """

    @staticmethod
    async def get_advertisement_by_id(advertisement_id: int) -> Advertisement | None:
        """
        Get advertisement by ID.

        :param advertisement_id: Advertisement ID.
        :return: Advertisement.
        """
        redis_client = await get_redis()
        try:
            advertisement = await redis_client.get(f"advertisement:{advertisement_id}")
        except aioredis.TimeoutError:
            advertisement = None

        if advertisement:
            return Advertisement(**json.loads(advertisement))

        async with get_session() as session:
            result = await session.execute(
                select(Advertisement)
                .where(Advertisement.id == advertisement_id)
            )
            advertisement = result.scalar_one_or_none()
            if advertisement:
                await redis_client.set(f"advertisement:{advertisement_id}", json.dumps(advertisement.to_dict()),
                                       ex=3600)
            return advertisement

    @staticmethod
    async def get_all_advertisements() -> list[Advertisement]:
        """
        Get all advertisements.

        :return: List of advertisements.
        """
        redis_client = await get_redis()
        try:
            advertisements = await redis_client.get("advertisements")
        except aioredis.TimeoutError:
            advertisements = None

        if advertisements:
            return [Advertisement(**adv) for adv in json.loads(advertisements)]

        async with get_session() as session:
            result = await session.execute(select(Advertisement))
            advertisements = result.scalars().all()
            await redis_client.set("advertisements", json.dumps([adv.to_dict() for adv in advertisements]), ex=3600)

            return advertisements

    @staticmethod
    async def get_advertisements_by_owner_id(owner_id: int) -> list[Advertisement]:
        """
        Get advertisements by owner ID.

        :param owner_id: Owner ID.
        :return: List of advertisements.
        """
        redis_client = await get_redis()
        try:
            advertisements = await redis_client.get(f"advertisements:owner:{owner_id}")
        except aioredis.TimeoutError:
            advertisements = None

        if advertisements:
            return [Advertisement(**adv) for adv in json.loads(advertisements)]

        async with get_session() as session:
            result = await session.execute(
                select(Advertisement)
                .where(Advertisement.owner_id == owner_id)
            )
            advertisements = result.scalars().all()
            await redis_client.set(f"advertisements:owner:{owner_id}",
                                   json.dumps([adv.to_dict() for adv in advertisements]), ex=3600)

            return advertisements

    @staticmethod
    async def get_owner_id_by_advertisement_id(advertisement_id: int) -> int | None:
        """
        Get owner ID by advertisement ID.

        :param advertisement_id: Advertisement ID.
        :return: Owner ID.
        """
        redis_client = await get_redis()
        try:
            owner_id = await redis_client.get(f"advertisement:owner:{advertisement_id}")
        except aioredis.TimeoutError:
            owner_id = None

        if owner_id:
            return int(owner_id)

        async with get_session() as session:
            owner_id = (await session.execute(
                select(Advertisement.owner_id)
                .where(Advertisement.id == advertisement_id)
            )).scalar_one_or_none()

            if owner_id:
                await redis_client.set(f"advertisement:owner:{advertisement_id}", owner_id, ex=3600)

            return owner_id

    @staticmethod
    async def get_media_files(advertisement_id: int) -> list[MediaFile]:
        """
        Get media files of an advertisement.

        :param advertisement_id: Advertisement ID.
        :return: List of media files.
        """
        redis_client = await get_redis()
        try:
            media_files = await redis_client.get(f"advertisement:media:{advertisement_id}")
        except aioredis.TimeoutError:
            media_files = None

        if media_files:
            return [MediaFile(**mf) for mf in json.loads(media_files)]

        async with get_session() as session:
            result = await session.execute(
                select(MediaFile).where(MediaFile.advertisement_id == advertisement_id)
            )
            media_files = result.scalars().all()
            await redis_client.set(f"advertisement:media:{advertisement_id}",
                                   json.dumps([mf.to_dict() for mf in media_files]), ex=3600)

            return media_files

    @staticmethod
    async def get_requested_ads() -> list[Advertisement]:
        """
        Get requested advertisements.

        :return: List of advertisements.
        """
        redis_client = await get_redis()
        try:
            requested_ads = await redis_client.get("advertisements:requested")
        except aioredis.TimeoutError:
            requested_ads = None

        if requested_ads:
            return [Advertisement(**adv) for adv in json.loads(requested_ads)]

        async with get_session() as session:
            result = await session.execute(
                select(Advertisement)
                .where(Advertisement.status == 'pending')
            )
            requested_ads = result.scalars().all()
            await redis_client.set("advertisements:requested", json.dumps([adv.to_dict() for adv in requested_ads]),
                                   ex=3600)

            return requested_ads

    @staticmethod
    async def create_advertisement(owner_id: int, **kwargs) -> Advertisement:
        """
        Create an advertisement.

        :param owner_id: Owner ID.
        :param kwargs: Advertisement data.
        :return: Created advertisement.
        """
        redis_client = await get_redis()
        async with get_session() as session:
            advertisement = Advertisement(
                owner_id=owner_id,
                **kwargs
            )

            session.add(advertisement)
            await session.commit()

            await redis_client.delete("advertisements")
            await redis_client.delete(f"advertisements:owner:{owner_id}")
            await redis_client.set(f"advertisement:{advertisement.id}", json.dumps(advertisement.to_dict()), ex=3600)

            return advertisement

    @staticmethod
    async def create_user_advertisement(user_id: int, advertisement_id: int) -> UserAdvertisement:
        """
        Create a user advertisement.

        :param user_id: User ID.
        :param advertisement_id: Advertisement ID.
        :return: Created user advertisement.
        """
        async with get_session() as session:
            user_advertisement = UserAdvertisement(
                user_id=user_id,
                advertisement_id=advertisement_id
            )

            session.add(user_advertisement)
            await session.commit()

            return user_advertisement

    @staticmethod
    async def update_advertisement(advertisement_id: int, **kwargs) -> Advertisement | None:
        """
        Update an advertisement.

        :param advertisement_id: Advertisement ID.
        :param kwargs: Advertisement data.
        :return: Updated advertisement.
        """
        redis_client = await get_redis()
        try:
            await redis_client.delete(f"advertisement:{advertisement_id}")
            await redis_client.delete(f"advertisements:owner:{advertisement_id}")
            await redis_client.delete("advertisements")
        except aioredis.TimeoutError:
            pass

        async with get_session() as session:
            result = await session.execute(
                select(Advertisement)
                .where(Advertisement.id == advertisement_id)
            )
            advertisement = result.scalar_one_or_none()
            if advertisement:
                for key, value in kwargs.items():
                    setattr(advertisement, key, value)
                await session.commit()

                return advertisement

    @staticmethod
    async def update_advertisement_media(advertisement_id: int, media: list[dict]) -> None:
        """
        Update advertisement media.

        :param advertisement_id: Advertisement ID.
        :param media: List of media files.
        """
        redis_client = await get_redis()

        async with get_session() as session:
            result = await session.execute(
                select(MediaFile)
                .where(MediaFile.advertisement_id == advertisement_id)
            )
            existing_media = result.scalars().all()

            if existing_media:
                for media_file, new_media in zip(existing_media, media):
                    media_file.media_type = new_media['type']
                    media_file.file_id = new_media['file_id']

                if len(media) > len(existing_media):
                    new_media_entries = [
                        MediaFile(advertisement_id=advertisement_id, **m)
                        for m in media[len(existing_media):]
                    ]
                    session.add_all(new_media_entries)
            else:
                new_media_entries = [MediaFile(advertisement_id=advertisement_id, **m) for m in media]
                session.add_all(new_media_entries)

            await session.commit()

            await redis_client.delete(f"advertisement:media:{advertisement_id}")

    @staticmethod
    async def update_advertisement_status(advertisement_id: int, status: str) -> None:
        """
        Update advertisement status.

        :param advertisement_id: Advertisement ID.
        :param status: Status.
        """
        async with get_session() as session:
            advertisement = (await session.execute(
                select(Advertisement)
                .where(Advertisement.id == advertisement_id)
            )).scalar_one_or_none()

            if advertisement:
                advertisement.status = status
                await session.commit()

                redis_client = await get_redis()
                await redis_client.delete(f"advertisement:{advertisement_id}")
                await redis_client.delete(f"advertisements:owner:{advertisement.owner_id}")
                await redis_client.delete("advertisements")
                await redis_client.delete("advertisements:requested")

    @staticmethod
    async def delete_advertisement(advertisement_id: int) -> None:
        """
        Delete an advertisement.

        :param advertisement_id: Advertisement ID.
        """
        redis_client = await get_redis()
        async with get_session() as session:
            advertisement = (await session.execute(
                select(Advertisement)
                .where(Advertisement.id == advertisement_id)
            )).scalar_one_or_none()

            if advertisement:
                await session.delete(advertisement)
                await session.commit()

                await redis_client.delete(f"advertisement:{advertisement_id}")
                await redis_client.delete(f"advertisements:owner:{advertisement.owner_id}")
