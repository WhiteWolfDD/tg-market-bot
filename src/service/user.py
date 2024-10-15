import hashlib

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from src.database import get_session
from src.models.user import User


class UserService:
    """
    User service.
    """

    @staticmethod
    async def get_user_by_tg_id(user_id: int) -> User | None:
        """
        Get user by Telegram ID.

        :param user_id: Telegram user ID.
        :return: User.
        """

        async with get_session() as session:
            return (await session.execute(
                select(User)
                .where(User.telegram_user_id == user_id)
            )).scalar_one_or_none()

    @classmethod
    async def get_all_users(cls) -> list[User]:
        """
        Get all users.

        :return: List of users.
        """

        async with get_session() as session:
            return (await session.execute(
                select(User)
            )).scalars().all()

    @staticmethod
    async def get_user_by_id(user_id: int) -> User | None:
        """
        Get user by ID.

        :param user_id: User ID.
        :return: User.
        """

        async with get_session() as session:
            return (await session.execute(
                select(User)
                .where(User.id == user_id)
            )).scalar_one_or_none()

    @staticmethod
    async def update(user_id: int, **kwargs) -> User | None:
        """
        Update user.

        :param user_id: User ID.
        :param kwargs: User fields.
        :return: Updated user.
        """

        async with get_session() as session:
            user = (await session.execute(
                select(User)
                .where(User.id == user_id)
            )).scalar_one_or_none()

            if user:
                for key, value in kwargs.items():
                    setattr(user, key, value)

                await session.commit()

            return user

    @staticmethod
    async def create_user(user_id: int) -> User:
        """
        Create user.

        :param user_id: Telegram user ID.
        :return: User.
        """

        async with get_session() as session:
            user = User(
                telegram_user_id=user_id
            )

            session.add(user)
            await session.commit()

            return user
