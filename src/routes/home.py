import os
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from src.callbacks.admin import ViewExceptionLogCallback, DeleteExceptionLogsCallback
from src.routes.advertisement import start_post_ad
from src.routes.category import show_categories, get_categories
from src.utils.helpers import escape_markdown

router = Router()


async def home_page(fullname: str, is_admin: bool = False) -> tuple[str, ReplyKeyboardMarkup]:
    """
    Отображает домашнюю страницу с проверкой на администратора.
    """
    msg = (
        _("👋 Hello, *{username}*.\nI'm *Seller — curator of your ads*.\n\n"
          '🌟 Here you can post your *ads* for *selling* your product.')
    ).format(username=fullname)

    # Основные кнопки для всех пользователей
    keyboard_buttons = [
        [KeyboardButton(text=_('📤 Post an ad')), KeyboardButton(text=_('📦 My ads'))],
        [KeyboardButton(text='📚 FAQ'), KeyboardButton(text=_('🌐 Language'))]
    ]

    # Если пользователь — администратор, добавляем дополнительные кнопки
    if is_admin:
        keyboard_buttons.insert(1, [KeyboardButton(text=_('📦 Requested ads')), KeyboardButton(text=_('📜 Error logs'))])
        keyboard_buttons.insert(2,
                                [KeyboardButton(text=_('📝 Manage Categories')), KeyboardButton(text=_('📊 Statistics'))])

    kbd = ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True
    )

    return msg, kbd


@router.message(CommandStart())
async def start(message: Message, state: FSMContext) -> None:
    """
    Handler for the /start command.
    """

    # Проверка deep_link
    deep_link = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else None
    if deep_link == "post_ad":
        await start_post_ad(message, state)
    else:
        await go_home(message, state)


async def go_home(message: Message, state: FSMContext) -> None:
    """
    Отображение главной страницы в зависимости от прав доступа (админ/пользователь).
    """
    if state:
        await state.clear()

    # Проверяем, является ли пользователь администратором
    admins = os.getenv('ADMIN_ID').split(',')
    is_admin = str(message.from_user.id) in admins

    # Генерируем сообщение и клавиатуру
    msg, kbd = await home_page(fullname=message.from_user.full_name, is_admin=is_admin)

    # Отправляем сообщение с клавиатурой
    await message.answer(escape_markdown(text=msg), reply_markup=kbd)


@router.message(F.text == __('📝 Manage Categories'))
async def handle_manage_categories(message: Message, state: FSMContext) -> None:
    """
    Обработка команды управления категориями (доступно только для администраторов).
    """
    admins = os.getenv('ADMIN_ID').split(',')
    if str(message.from_user.id) in admins:
        await manage_categories(message, state)
    else:
        await message.answer(
            text=escape_markdown(
                _('❌ You do not have access to this command.')
            )
        )


@router.message(F.text == __('📦 Requested ads'))
@router.message(F.text == __('📜 Error logs'))
async def handle_admin_commands(message: Message) -> None:
    """
    Обработка команд администратора.
    """
    admins = os.getenv('ADMIN_ID').split(',')
    if str(message.from_user.id) not in admins:
        await message.answer(
            text=escape_markdown(
                _('❌ You do not have access to this command.')
            )
        )
        return

    if message.text == _('📜 Error logs'):
        await view_exception_logs(message)
    elif message.text == _('📦 Requested ads'):
        await message.answer(
            text=escape_markdown(
                _('🚧 This feature is under construction.')
            )
        )


async def manage_categories(message: Message, state: FSMContext) -> None:
    """
    Управление категориями администратора.
    """
    categories = await get_categories()
    await state.clear()
    await state.update_data(categories=categories)
    user_language = message.from_user.language_code or 'en'
    await show_categories(message, categories, user_language, state, parent_id=None)


@router.message(F.text == __('📜 Error logs'))
async def view_exception_logs(message: Message) -> None:
    """Обработка команды для просмотра логов от администратора через сообщение."""
    await message.answer(
        text=escape_markdown(
            _('📜 *Exception Logs*\n\n🚧 This feature is under construction.')
        )
    )


@router.callback_query(DeleteExceptionLogsCallback.filter())
async def delete_exception_logs(query: CallbackQuery) -> None:
    """Удаление логов ошибок (только для администраторов)."""
    await query.answer(
        text=escape_markdown(
            _('🚧 This feature is under construction.')
        )
    )


@router.callback_query(ViewExceptionLogCallback.filter())
async def view_exception_log(query: CallbackQuery) -> None:
    """Просмотр лога ошибки (только для администраторов)."""
    await query.answer(
        text=escape_markdown(
            _('🚧 This feature is under construction.')
        )
    )
