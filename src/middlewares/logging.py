from datetime import datetime

from aiogram import BaseMiddleware


class LoggingMiddleware(BaseMiddleware):
    """
    Middleware for logging each request (access level).
    """

    async def __call__(self, handler, event, data):
        """
        Make some logging before handling the request.
        """

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        msg = f"[{date}] {event}"

        with open("storage/logs/access.log", "a") as file:
            file.write(msg + "\n")

        return await handler(event, data)
