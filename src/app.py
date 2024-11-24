import os
import asyncio

from src.middlewares.response_time import ResponseTimeMiddleware
from src.middlewares.user_activity import UserActivityMiddleware
from src.middlewares.user_middleware import UserMiddleware
from src.utils.localization import setup_i18n
from src.utils.log import setup_logging
from src.utils.tasks import database_test_connection
from src.utils.scheduler import start_scheduler

from aiogram import Dispatcher, Bot, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware

logger = setup_logging()


class Application:
    """
    Bootstrap the application.
    """

    def __init__(self) -> None:
        """
        Constructor.
        """
        storage = MemoryStorage()
        self.__dispatcher = Dispatcher(storage=storage)
        self.__dispatcher.update.middleware(ResponseTimeMiddleware())
        self.__dispatcher.update.middleware(UserMiddleware())
        self.__dispatcher.update.middleware(UserContextMiddleware())
        self.__dispatcher.update.middleware(UserActivityMiddleware())

        setup_i18n(self.__dispatcher)

        self.__router = self.__include_router()

        self.__bot = Bot(
            token=os.getenv("BOT_TOKEN"),
            default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
        )

        self.__init_exception_handler()

    def __include_router(self) -> Router:
        """
        Include the router.
        """
        from src.routes.main import router

        self.__dispatcher.include_router(router)
        return router

    async def start(self) -> None:
        """
        Start the application.
        """
        if not await database_test_connection():
            print("Database connection failed.")
            return

        await self.__bot.delete_webhook(drop_pending_updates=True)

        await self.__initialize_statistics()

        # Start the scheduler
        scheduler = start_scheduler()

        try:
            await self.__dispatcher.start_polling(self.__bot)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down...")
        finally:
            scheduler.shutdown()
            await self.__bot.session.close()
            await self.__dispatcher.fsm.storage.close()

        # Check if Telegram API is available
        retry_delay = 1
        max_delay = 60

        while retry_delay <= max_delay:
            try:
                await self.__dispatcher.start_polling(self.__bot)
                break  # Exit loop if polling starts successfully
            except TelegramNetworkError as e:
                print(f"Network error: {e}. Retrying in {retry_delay} seconds...")
            except Exception as e:
                print(f"Unexpected error: {e}. Retrying in {retry_delay} seconds...")

            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, max_delay)  # Exponential backoff

    def __init_exception_handler(self) -> None:
        """
        Initialize the exception handler.
        """
        from src.middlewares.errors import ErrorsMiddleware

        middleware = ErrorsMiddleware()
        self.__router.message.middleware(middleware)
        self.__router.callback_query.middleware(middleware)

    @staticmethod
    async def __initialize_statistics():
        from src.database import get_session
        from src.models import Statistic

        async with get_session() as session:
            statistic = await session.get(Statistic, 1)
            if not statistic:
                statistic = Statistic(id=1)
                session.add(statistic)
                await session.commit()
