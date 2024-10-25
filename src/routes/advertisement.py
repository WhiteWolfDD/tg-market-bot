from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from src.routes.category import show_categories, get_categories
from src.utils.helpers import escape_markdown
from src.utils.log import setup_logging
from src.utils.states import PostAdStates

router = Router()
logger = setup_logging()


@router.message(Command(commands=['cancel']))
async def cancel_post_ad(message: Message, state: FSMContext) -> None:
    """
    Cancel the operation.
    """

    await state.clear()
    await message.answer(
        escape_markdown(text=_('🚫 Operation canceled.')),
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.text == __('📤 Post an ad'))
async def start_post_ad(message: Message, state: FSMContext) -> None:
    """
    Start posting an advertisement.
    """

    await message.answer(
        escape_markdown(
            text=_('📤 *Post an ad*\n\n📝 Send me the *title* of the ad.\n\n🚫 Send /cancel to cancel the operation.')),
        reply_markup=ReplyKeyboardRemove()
    )



    await state.set_state(PostAdStates.TITLE)


@router.message(PostAdStates.TITLE)
async def post_ad_title(message: Message, state: FSMContext) -> None:
    """
    Receive ad title.
    """

    await state.update_data(title=message.text)
    await message.answer(
        escape_markdown(text=_(
            '📤 *Post an ad*\n\n📝 Send me the *description* of the ad.\n\n🚫 Send /cancel to cancel the operation.')),
    )

    await state.set_state(PostAdStates.DESCRIPTION)


@router.message(PostAdStates.DESCRIPTION)
async def post_ad_description(message: Message, state: FSMContext) -> None:
    """
    Receive ad description.
    """

    await state.update_data(description=message.text)
    await message.answer(
        escape_markdown(
            text=_('📤 *Post an ad*\n\n💵 Send me the *price* of the ad.\n\n🚫 Send /cancel to cancel the operation.')),
    )

    await state.set_state(PostAdStates.PRICE)


@router.message(PostAdStates.PRICE)
async def post_ad_price(message: Message, state: FSMContext) -> None:
    """
    Receive ad price and start category selection.
    """

    await state.update_data(price=message.text)
    user_language = message.from_user.language_code or 'en'
    categories = await get_categories()
    await state.update_data(categories=categories)
    await show_categories(message, categories, user_language, state, parent_id=None)
