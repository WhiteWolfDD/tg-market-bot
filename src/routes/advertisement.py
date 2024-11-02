from decimal import Decimal, InvalidOperation
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from src.schemas.advertisement import AdvertisementModel, ValidationError, translate_validation_error
from src.routes.category import show_categories, get_categories
from src.utils.helpers import escape_markdown
from src.utils.log import setup_logging
from src.utils.states import PostAdStates

router = Router()
logger = setup_logging()


def validation_error_handler(func):
    """
    Decorator function to handle ValidationError.

    :param func: Function
    :return: Wrapper function
    """

    async def wrapper(message: Message, state: FSMContext):
        try:
            return await func(message, state)
        except ValidationError as e:
            await message.answer(
                escape_markdown(text=translate_validation_error(e)),
            )

    return wrapper


@router.message(Command(commands=['cancel']))
async def cancel_post_ad(message: Message, state: FSMContext) -> None:
    """
    Cancel the post-ad operation.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """

    await state.clear()
    await message.answer(
        escape_markdown(text=_('🚫 Operation canceled.')),
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(F.text == __('📤 Post an ad'))
async def start_post_ad(message: Message, state: FSMContext) -> None:
    """
    Start the post-ad operation.

    :param message: Message object
    :param state: FSMContext object
    :return: None
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
    Get the title of the ad.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """

    validation_error_handler(AdvertisementModel(title=message.text))

    await state.update_data(title=message.text)
    await message.answer(
        escape_markdown(text=_(
            '📤 *Post an ad*\n\n📝 Send me the *description* of the ad.\n\n🚫 Send /cancel to cancel the operation.')),
    )
    await state.set_state(PostAdStates.DESCRIPTION)


@router.message(PostAdStates.DESCRIPTION)
async def post_ad_description(message: Message, state: FSMContext) -> None:
    """
    Get the description of the ad.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """

    validation_error_handler(AdvertisementModel(description=message.text))

    await state.update_data(description=message.text)
    await message.answer(
        escape_markdown(
            text=_('📤 *Post an ad*\n\n💵 Send me the *price* of the ad.\n\n🚫 Send /cancel to cancel the operation.')),
    )
    await state.set_state(PostAdStates.PRICE)


@router.message(PostAdStates.PRICE)
async def post_ad_price(message: Message, state: FSMContext) -> None:
    """
    Get the price of the ad.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """

    price = message.text
    try:
        price_decimal = Decimal(price)
        if price_decimal.as_tuple().exponent != -2:
            raise ValueError
    except (ValueError, InvalidOperation):
        await message.answer(
            escape_markdown(text=_('💵 Please enter a valid price with 2 decimal places.')),
        )
        return

    validation_error_handler(AdvertisementModel(price=price_decimal))

    await state.update_data(price=price_decimal)
    user_language = message.from_user.language_code or 'en'
    categories = await get_categories()
    await state.update_data(categories=categories)
    await show_categories(message, categories, user_language, state, parent_id=None)
