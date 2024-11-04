import os

from src.middlewares.logging import LoggingMiddleware
from src.middlewares.user_middleware import UserMiddleware
from src.utils.localization import setup_i18n

from aiogram import Dispatcher, Bot, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares.user_context import UserContextMiddleware


async def database_test_connection() -> bool:
    """
    Test the connection to the database.
    :return: True if the connection is successful, otherwise False.
    """
    from src.database import test_connection

    try:
        await test_connection()
        return True
    except Exception as e:
        print(e)
        return False


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
        self.__dispatcher.update.middleware(UserMiddleware())
        self.__dispatcher.update.middleware(UserContextMiddleware())
        self.__dispatcher.update.middleware(LoggingMiddleware())

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
        from src.routes import router

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
        await self.__dispatcher.start_polling(
            self.__bot
        )

    def __init_exception_handler(self) -> None:
        """
        Initialize the exception handler.
        """
        from src.middlewares.errors import ErrorsMiddleware

        middleware = ErrorsMiddleware()
        self.__router.message.middleware(middleware)
        self.__router.callback_query.middleware(middleware)
