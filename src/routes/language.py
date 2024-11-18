from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.i18n import gettext as _, get_i18n
from aiogram.utils.i18n import lazy_gettext as __

from src.routes.home import start
from src.services.user import UserService
from src.utils.helpers import escape_markdown
from src.utils.log import setup_logging

router = Router()
logger = setup_logging()


@router.message(F.text == __('🌐 Language'))
async def handle_language_command(message: Message) -> None:
    """
    Обработка команды для смены языка.
    """

    await message.answer(
        text=escape_markdown(
            _('🌐 *Select your language*'),
        ),
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text='🇷🇺 Русский'),
                    KeyboardButton(text='🇺🇸 English'),
                    KeyboardButton(text='🇪🇪 Eesti'),
                ],
            ],
            resize_keyboard=True
        )
    )
    try:
        await message.delete()
    except Exception as e:
        logger.error(f'Error while deleting message: {e}')


async def set_language(message: Message, locale: str, state: FSMContext) -> None:
    """
    Установка языка.
    """
    # Сохраняем новый язык пользователя
    await UserService.set_user_locale(user_id=message.from_user.id, locale=locale)

    # Устанавливаем новый контекст локализации
    i18n = get_i18n()
    i18n.ctx_locale.set(locale)

    # Отправляем сообщение пользователю на новом языке
    text = _('🌐 *Language successfully changed.*\n\n🔄 Restarting the bot...')
    await message.answer(
        text=escape_markdown(text)
    )

    # Перезапускаем бота
    await start(message, state)


@router.message(F.text == '🇷🇺 Русский')
async def set_language_ru(message: Message, state: FSMContext) -> None:
    await set_language(message, 'ru', state)


@router.message(F.text == '🇺🇸 English')
async def set_language_en(message: Message, state: FSMContext) -> None:
    await set_language(message, 'en', state)


@router.message(F.text == '🇪🇪 Eesti')
async def set_language_et(message: Message, state: FSMContext) -> None:
    await set_language(message, 'et', state)
