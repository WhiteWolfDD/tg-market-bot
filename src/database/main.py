"""
Configuration file to create (async) connection to the database.
"""

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.utils.singleton import SingletonMeta

# Read the environment variables.
load_dotenv()

# Create a MySQL connection to the database.
metadata = MetaData()
Base = declarative_base()

# Create the engine.
class DatabaseEngine(metaclass=SingletonMeta):
    def __init__(self):
        self._engine = create_async_engine(
            url=os.getenv("DATABASE_URL"),
            future=True,
            echo=True
        )

    def get_engine(self):
        return self._engine

# Create the session.
async_session = async_sessionmaker(
    bind=DatabaseEngine().get_engine(),
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)


async def test_connection() -> None:
    """
    Test the connection to the database.
    """

    try:
        async with DatabaseEngine().get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        raise RuntimeError(f"An error occurred while connecting to the database: {e}")


@asynccontextmanager
async def get_session() -> AsyncSession:
    """
    Get the session.
    """

    async with async_session() as session:
        yield session
