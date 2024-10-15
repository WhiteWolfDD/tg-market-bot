from sqlalchemy import select

from src.database import get_session
from src.models.advertisement import Advertisement


class AdvertisementService:
    """
    Advertisement service.
    """

    @staticmethod
    async def get_advertisement_by_id(advertisement_id: int) -> Advertisement | None:
        """
        Get advertisement by ID.

        :param advertisement_id: Advertisement ID.
        :return: Advertisement.
        """

        async with get_session() as session:
            return (await session.execute(
                select(Advertisement)
                .where(Advertisement.id == advertisement_id)
            )).scalar_one_or_none()

    @staticmethod
    async def get_all_advertisements() -> list[Advertisement]:
        """
        Get all advertisements.

        :return: List of advertisements.
        """

        async with get_session() as session:
            return (await session.execute(
                select(Advertisement)
            )).scalars().all()

    @staticmethod
    async def get_advertisements_by_owner_id(owner_id: int) -> list[Advertisement]:
        """
        Get advertisements by owner ID.

        :param owner_id: Owner ID.
        :return: List of advertisements.
        """

        async with get_session() as session:
            return (await session.execute(
                select(Advertisement)
                .where(Advertisement.owner_id == owner_id)
            )).scalars().all()

    @staticmethod
    async def create_advertisement(owner_id: int, **kwargs) -> Advertisement:
        """
        Create an advertisement.

        :param owner_id: Owner ID.
        :param kwargs: Advertisement data.
        :return: Created advertisement.
        """

        async with get_session() as session:
            advertisement = Advertisement(
                owner_id=owner_id,
                **kwargs
            )

            session.add(advertisement)
            await session.commit()

            return advertisement

    @staticmethod
    async def update_advertisement(advertisement_id: int, **kwargs) -> Advertisement | None:
        """
        Update an advertisement.

        :param advertisement_id: Advertisement ID.
        :param kwargs: Advertisement data.
        :return: Updated advertisement.
        """

        async with get_session() as session:
            advertisement = (await session.execute(
                select(Advertisement)
                .where(Advertisement.id == advertisement_id)
            )).scalar_one_or_none()

            if advertisement:
                for key, value in kwargs.items():
                    setattr(advertisement, key, value)

                await session.commit()

            return advertisement

    @staticmethod
    async def delete_advertisement(advertisement_id: int) -> None:
        """
        Delete an advertisement.

        :param advertisement_id: Advertisement ID.
        """

        async with get_session() as session:
            advertisement = (await session.execute(
                select(Advertisement)
                .where(Advertisement.id == advertisement_id)
            )).scalar_one_or_none()

            if advertisement:
                session.delete(advertisement)
                await session.commit()
