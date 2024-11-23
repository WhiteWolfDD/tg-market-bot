import os
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from src.routes.admin import manage_categories, view_statistics, view_requested_ads, view_exception_logs
from src.routes.advertisement import start_post_ad
from src.utils.helpers import escape_markdown

router = Router()


def is_admin(user_id: int) -> bool:
    admins = os.getenv('ADMIN_ID').split(',')
    for admin in admins:
        if int(admin) == user_id:
            return True
    return False


async def home_page(fullname: str, message: Message) -> tuple[str, ReplyKeyboardMarkup]:
    """
    Show the home page.
    """

    msg = (
        _("👋 Hello, *{username}*.\nI'm *Seller — curator of your ads*.\n\n"
          '🌟 Here you can post your *ads* for *selling* your product.')
    ).format(username=fullname)

    # Keyboard buttons for users
    keyboard_buttons = [
        [KeyboardButton(text=_('📤 Post an ad')), KeyboardButton(text=_('📦 My ads'))],
        [KeyboardButton(text='📚 FAQ'), KeyboardButton(text=_('🌐 Language'))]
    ]

    # Keyboard buttons for admins
    if is_admin(message.from_user.id):
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

    # Deep linking support
    deep_link = message.text.split(" ")[1] if len(message.text.split(" ")) > 1 else None
    if deep_link == "post_ad":
        await start_post_ad(message, state)
    else:
        await go_home(message, state)


async def go_home(message: Message, state: FSMContext) -> None:
    """
    Go to the home page.
    """

    if state:
        await state.clear()

    msg, kbd = await home_page(fullname=message.from_user.full_name, message=message)
    await message.answer(escape_markdown(text=msg), reply_markup=kbd)


@router.message(F.text.in_([__('📝 Manage Categories'), __('📦 Requested ads'), __('📜 Error logs'), __('📊 Statistics')]))
async def handle_admin_commands(message: Message, state: FSMContext) -> None:
    """
    Handle admin commands.
    """
    if not is_admin(message.from_user.id):
        await message.answer(
            text=escape_markdown(
                _('❌ You do not have access to this command.')
            )
        )
        return

    if message.text == _('📝 Manage Categories'):
        await manage_categories(message, state)
    elif message.text == _('📜 Error logs'):
        await view_exception_logs(message)
    elif message.text == _('📦 Requested ads'):
        await view_requested_ads(message)
    elif message.text == _('📊 Statistics'):
        await view_statistics(message)
