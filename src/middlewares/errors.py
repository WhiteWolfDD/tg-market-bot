import os
import traceback
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, FSInputFile

from src.callbacks.main import DeleteMessageCallback
from src.utils.helpers import escape_markdown, build_inline_keyboard
from src.utils.log import setup_logging

logger = setup_logging()

class ErrorsMiddleware(BaseMiddleware):
    """
    Middleware class for handling exceptions and sending logs to the admin.
    """
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            admins = os.getenv("ADMIN_ID").split(",")
            chat_id = None

            # Get the chat ID from the event
            if isinstance(event, Message):
                chat_id = event.chat.id
            elif isinstance(event, CallbackQuery):
                chat_id = event.message.chat.id

            if chat_id and str(chat_id) not in admins:
                msg = (
                    '😕 *Oops!*\n\n'
                    'Something went wrong while processing your request. Please try again later.\n\n'
                    'Our team has been notified about this error.'
                )

                client_msg = await event.bot.send_message(
                    chat_id=chat_id,
                    text=escape_markdown(text=msg),
                )

                kbd = {
                    'inline_kbd': [
                        [
                            {'text': '🫣 Hide',
                             'callback_data': DeleteMessageCallback(message_id=client_msg.message_id).pack()},
                        ]
                    ]
                }

                await event.bot.edit_message_reply_markup(
                    chat_id=client_msg.chat.id,
                    message_id=client_msg.message_id,
                    reply_markup=build_inline_keyboard(keyboard=kbd).as_markup()
                )

            # Save the exception log to a file
            filename = f"{int(datetime.now().timestamp())}.log"
            with open(f"storage/logs/exceptions/{filename}", "w", encoding='utf-8') as file:
                file.write(traceback.format_exc())

            # Send the exception log to the admin
            for admin in admins:
                msg = (
                    '💥 *A new error has occurred!*\n\n'
                    'Exception log is attached below.'
                )

                kbd = {'inline_kbd': []}

                log_file = FSInputFile(f"storage/logs/exceptions/{filename}", filename="exception.log")

                await event.bot.send_document(
                    chat_id=admin,
                    document=log_file,
                    caption=escape_markdown(text=msg),
                    reply_markup=build_inline_keyboard(keyboard=kbd, home_button=True).as_markup()
                )