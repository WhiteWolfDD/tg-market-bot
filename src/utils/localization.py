from aiogram.utils.i18n import I18n
from aiogram.utils.i18n.middleware import I18nMiddleware
from typing import Any, Dict
from aiogram.types import TelegramObject, User

from src.utils.cache import get_user_locale


def get_i18n():
    return i18n


class CustomI18nMiddleware(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        user: User = data.get('event_from_user')

        if user:
            user_id = user.id
            user_language = await get_user_locale(user_id)
            if user_language:
                return user_language

        return self.i18n.default_locale


i18n = I18n(
    path='src/locales',
    default_locale='en',
    domain='messages'
)


def setup_i18n(dispatcher):
    """
    Setup i18n middleware
    """
    dispatcher.update.middleware(CustomI18nMiddleware(i18n))
