import os
import re

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, ReplyKeyboardRemove, FSInputFile, InlineKeyboardMarkup,
    InlineKeyboardButton, Location, CallbackQuery
)
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.media_group import MediaGroupBuilder

from geopy import Nominatim
from typing import Tuple, Optional
from decimal import Decimal, InvalidOperation

from geopy.exc import GeopyError

from src.callbacks.admin import ApproveAdCallback, RejectAdCallback, ManageAdAdminCallback
from src.callbacks.advertisement import ConfirmAdCallback, CancelAdCallback
from src.handlers.advertisement import handle_media_upload
from src.models import MediaFile
from src.schemas.advertisement import AdvertisementSchema, ValidationError, translate_validation_error
from src.routes.category import show_categories
from src.services.advertisement import AdvertisementService
from src.services.category import CategoryService
from src.services.user import UserService
from src.utils.const import StoragePaths
from src.utils.helpers import escape_markdown, build_media_group, build_inline_keyboard
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
            text=_(
                '📤 *Post an ad*\n\n'
                '📝 Send me the *title* of the ad.\n'
                '✍️ e.g. iPhone 16 Pro Max\n\n'
                '🚫 Send /cancel to cancel the operation.')),
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

    validation_error_handler(AdvertisementSchema(title=message.text))

    await state.update_data(title=message.text)
    await message.answer(
        escape_markdown(text=_(
            '📤 *Post an ad*\n\n'
            '📝 Send me the *description* of the ad.\n'
            '✍️ e.g. Brand new iPhone 16 Pro Max with 512GB.\n\n'
            '🚫 Send /cancel to cancel the operation.'))
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

    validation_error_handler(AdvertisementSchema(description=message.text))

    await state.update_data(description=message.text)
    await message.answer(
        escape_markdown(
            text=_(
                '📤 *Post an ad*\n\n'
                '📝 Please provide the *reason for selling*.\n'
                '✍️ e.g. I need money for my tuition fees.\n\n'
                '🚫 Send /cancel to cancel the operation.'))
    )
    await state.set_state(PostAdStates.REASON)


@router.message(PostAdStates.REASON)
async def post_ad_reason(message: Message, state: FSMContext) -> None:
    """
    Get the reason of the ad.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """

    validation_error_handler(AdvertisementSchema(reason=message.text))

    await state.update_data(reason=message.text)
    await message.answer(
        escape_markdown(
            text=_(
                '📤 *Post an ad*\n\n'
                '💵 Send me the *price* of the ad in euro.\n'
                '✍️ e.g. 699.99\n\n'
                '🚫 Send /cancel to cancel the operation.'))
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

    price = re.sub(r'€|euro|eur', '', message.text, flags=re.IGNORECASE)
    try:
        price_decimal = Decimal(price)
        if price_decimal.as_tuple().exponent != -2:
            raise ValueError
    except (ValueError, InvalidOperation):
        await message.answer(
            escape_markdown(text=_('💵 Please enter a valid price with 2 decimal places.')),
        )
        return

    validation_error_handler(AdvertisementSchema(price=price_decimal))

    await state.update_data(price=price_decimal)
    user_language = message.from_user.language_code or 'en'
    categories = await CategoryService.get_categories()
    await state.update_data(categories=categories)
    await show_categories(message, categories, user_language, state, parent_id=None)


@router.message(PostAdStates.MEDIA)
async def post_ad_media(message: Message, state: FSMContext) -> None:
    """
    Handle media upload for the advertisement.
    """
    await handle_media_upload(message, state)


@router.message(PostAdStates.LOCATION)
async def post_ad_location(message: Message, state: FSMContext) -> None:
    """
    Get the location of the advertisement.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    if message.content_type == 'location':
        location = message.location
    else:
        location = message.text

    await state.update_data(location=location)
    await message.answer(
        escape_markdown(_('📎 Send me the *contact information* of the ad.')),
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(PostAdStates.CONTACT_INFO)


@router.message(PostAdStates.CONTACT_INFO)
async def post_ad_contact_info(message: Message, state: FSMContext) -> None:
    """
    Get the contact information of the advertisement.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    contact_info = message.text
    await state.update_data(contact_info=contact_info)
    await message.answer(escape_markdown(_('📤 *Post an ad*\n\n'
                                           '☕️ *Please wait while I process your ad...*')))
    await finish_post_ad(message, state)


async def finish_post_ad(message: Message, state: FSMContext) -> None:
    """
    Finish the post-ad operation.
    In this function, the advertisement is created via FSMContext and sent to the user.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    data = await state.get_data()
    title = data.get('title', '')
    description = data.get('description', '')
    reason = data.get('reason', '')
    price = data.get('price', '')
    selected_category = data.get('selected_category', {})
    media = data.get('media', [])
    contact_info = data.get('contact_info', '')
    location = data.get('location', '')

    media_files = await prepare_media_files(media)
    hashtags_text = await generate_hashtags(selected_category)
    location_text = await format_location(location)

    ad_text = (
        f"*Title:* {title}\n"
        f"*Description:* {description}\n"
        f"*Reason for Selling:* {reason}\n"
        f"*Price:* {price} €\n\n"
        f"*Contact Information:* {contact_info}\n"
        f"*Location:* {location_text}\n\n"
        f"{hashtags_text}"
    )

    if media_files:
        await send_media_group(message, media_files, ad_text)
    else:
        await message.answer(escape_markdown(ad_text))

    await confirm_ad_details(message)


async def confirm_ad_details(message: Message):
    """
    Confirm the advertisement details.

    :param message: Message object
    :return: None
    """
    await message.answer(
        escape_markdown(_('📤 *Post an ad*\n\n'
                          '👍 *Please confirm the details of your ad.*')),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('✅ Confirm'), callback_data=ConfirmAdCallback().pack())],
            [InlineKeyboardButton(text=_('🚫 Cancel'), callback_data=CancelAdCallback().pack())]
        ])
    )


@router.callback_query(ConfirmAdCallback.filter())
async def confirm_ad_callback(callback_query: CallbackQuery, state: FSMContext):
    """
    Confirm the advertisement.

    :param callback_query: CallbackQuery object
    :param state: FSMContext object
    :return: None
    """
    await callback_query.message.edit_text(
        escape_markdown(
            _(
                '📤 *Post an ad*\n\n'
                '👍 Your ad has been *successfully submitted for moderation*.\n\n'
                '🔍 You can check the *status* of your ad through the "My Ads" button in the ReplyKeyboard when you use the /start command.\n\n'
                '✅ If your ad *passes the moderation*, it will be *posted in the group* and you will be *notified immediately*.\n\n'
                '❌ If your ad *does not pass* the moderation, *you will be notified* as well.'
            )
        )
    )
    await callback_query.answer()

    data = await state.get_data()
    location = data.get('location', '')
    selected_category = data.get('selected_category', {})

    user_id = await UserService.get_user_id_by_telegram_id(callback_query.from_user.id)

    media_files = [
        MediaFile(file_id=item['file_id'], media_type=item['type'])
        for item in data.get('media', [])
    ]

    hashtags = await generate_hashtags(selected_category)
    location_text = await format_location(location)

    advertisement = await AdvertisementService.create_advertisement(
        owner_id=user_id,
        title=data.get('title', ''),
        description=data.get('description', ''),
        reason=data.get('reason', ''),
        price=data.get('price', ''),
        location=location_text,
        category_id=selected_category.get('id', 0),
        hashtags=hashtags.split(),
        media_files=media_files,
        contact_info=data.get('contact_info', '')
    )

    await AdvertisementService.create_user_advertisement(user_id=user_id, advertisement_id=advertisement.id)

    admin_id = os.getenv("ADMIN_ID")
    await send_ad_to_admin(
        advertisement=advertisement,
        admin_id=admin_id,
        bot=callback_query.bot
    )
    await state.clear()


@router.callback_query(CancelAdCallback.filter())
async def cancel_ad_callback(callback_query: CallbackQuery, state: FSMContext):
    """
    Cancel the advertisement.

    :param callback_query: CallbackQuery object
    :param state: FSMContext object
    :return: None
    """
    await state.clear()
    await callback_query.message.edit_text(
        escape_markdown(
            _(
                '🚫 *Ad Submission Canceled*\n\n'
                'Your ad submission has been *canceled*.\n\n'
                'To submit a new ad, please start the process again by selecting the "📤 Post an ad" button in the main menu.\n\n'
                'We look forward to seeing your ad soon! 😊'
            )
        )
    )
    await callback_query.answer()


async def generate_hashtags(selected_category):
    """
    Generate hashtags for the advertisement.

    :param selected_category: Dict
    :return: str
    """
    category_ids = [int(cid) for cid in selected_category.get('path', '').split('.') if cid]
    hashtags = []

    for category_id in category_ids:
        category = await CategoryService.get_category_by_id(category_id)
        for translation in category.get('translations', []):
            hashtag = f"#{translation['name'].replace(' ', '_').replace('&', '')}"
            hashtags.append(hashtag)

    return " ".join(hashtags)


async def format_location(location):
    """
    Format the location.

    :param location: Location object or str
    :return: str
    """
    if isinstance(location, Location):
        city, county, country = await get_location_info(location.latitude, location.longitude)
        return f"{city}, {county}, {country}" if all([city, county, country]) else _("Unknown location")
    elif isinstance(location, str):
        return location
    else:
        return _("Unknown location")


async def send_media_group(message: Message, media_files: list, caption: str):
    """
    Send the media group to the user.

    :param message: Message object
    :param media_files: List
    :param caption: str
    :return: None
    """
    media_group = MediaGroupBuilder(caption=escape_markdown(caption))

    for media_file in media_files:
        if media_file['type'] == 'photo':
            media_group.add_photo(media=media_file['file'])
        elif media_file['type'] == 'video':
            media_group.add_video(media=media_file['file'])

    try:
        await message.answer_media_group(media=media_group.build())
    except Exception as e:
        logger.error(f"Error sending media group: {e}")
        await message.answer(escape_markdown(caption))


async def load_media(file_path) -> FSInputFile:
    """
    Load the media file from the server storage.

    :param file_path: str
    :return: FSInputFile object
    """
    return FSInputFile(file_path)


async def get_location_info(latitude: float, longitude: float) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Get the location information based on the latitude and longitude.

    :param latitude: The latitude of the location
    :param longitude: The longitude of the location
    :return: Tuple containing city, county, and country as Optional strings
    """
    geolocator = Nominatim(user_agent="advertisement_bot")

    try:
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
    except (Exception, GeopyError) as e:
        print(f"Error occurred while retrieving location info: {e}")
        return None, None, None

    if location:
        address = location.raw.get('address', {})
        city = address.get('city') or address.get('town') or address.get('village') or address.get('hamlet')
        county = address.get('county') or address.get('state')
        country = address.get('country')

        return city, county, country

    return None, None, None


async def prepare_media_files(media: list) -> list:
    """
    Prepare media files for sending to the user.

    :param media: List
    :return: List
    """
    media_files = []
    for item in media:
        media_type = item['type']
        file_id = item['file_id']
        if media_type == 'photo':
            media_path = os.path.join(StoragePaths.PHOTO_PATH, f"{file_id}.jpg")
        elif media_type == 'video':
            media_path = os.path.join(StoragePaths.VIDEO_PATH, f"{file_id}.mp4")
        else:
            continue

        if os.path.exists(media_path):
            media_file = await load_media(media_path)
            media_files.append({'file': media_file, 'type': media_type})
    return media_files


async def send_ad_to_admin(advertisement, admin_id, bot: Bot):
    """
    Send the advertisement to the admin for approval.

    :param advertisement: Advertisement object
    :param admin_id: Admin Telegram ID
    :param bot: Bot instance
    """
    hashtags = " ".join(advertisement.hashtags)

    ad_text = (
        f"*Title:* {advertisement.title}\n"
        f"*Description:* {advertisement.description}\n"
        f"*Reason for Selling:* {advertisement.reason}\n"
        f"*Price:* {advertisement.price} €\n\n"
        f"*Contact Information:* {advertisement.contact_info}\n"
        f"*Location:* {advertisement.location}\n\n"
        f"{hashtags}"
    )

    media_group = await build_media_group(advertisement.id, ad_text)

    kbd = build_inline_keyboard(
        keyboard={
            'inline_kbd': [
                [
                    {'text': _('✅ Approve'), 'callback_data': ApproveAdCallback(ad_id=advertisement.id).pack()},
                    {'text': _('🔧 Manage'), 'callback_data': ManageAdAdminCallback(ad_id=advertisement.id).pack()},
                    {'text': _('❌ Reject'), 'callback_data': RejectAdCallback(ad_id=advertisement.id).pack()}
                ]
            ]
        }
    )

    try:
        await bot.send_media_group(chat_id=admin_id, media=media_group.build())
        await bot.send_message(
            chat_id=admin_id,
            text=escape_markdown(_('🎟 Please approve or reject this ad:')),
            reply_markup=kbd.as_markup()
        )
    except Exception as e:
        logger.error(f"Failed to send media group: {e}")
        await bot.send_message(
            chat_id=admin_id,
            text=escape_markdown(ad_text),
            reply_markup=kbd.as_markup()
        )
