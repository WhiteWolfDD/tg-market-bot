import os
from decimal import Decimal, InvalidOperation

import cv2
from PIL import Image
from aiogram import Router, F, Bot
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, \
    KeyboardButton, ReplyKeyboardMarkup, Location, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.media_group import MediaGroupBuilder
from geopy import Nominatim
from moviepy.editor import VideoFileClip

from src.callbacks.advertisement import AddMediaCallback, FinishUploadMediaCallback
from src.schemas.advertisement import AdvertisementModel, ValidationError, translate_validation_error
from src.routes.category import show_categories
from src.service.category import CategoryService
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
            text=_(
                '📤 *Post an ad*\n\n📝 Send me the *title* of the ad.\n✍️ e.g. iPhone 16 Pro Max\n\n🚫 Send /cancel to cancel the operation.')),
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
            '📤 *Post an ad*\n\n📝 Send me the *description* of the ad.\n✍️ e.g. Brand new iPhone 16 Pro Max with 512GB.\n\n🚫 Send /cancel to cancel the operation.'))
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
            text=_(
                '📤 *Post an ad*\n\n📝 Please provide the *reason for selling*.\n✍️ e.g. I need money for my tuition fees.\n\n🚫 Send /cancel to cancel the operation.'))
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

    validation_error_handler(AdvertisementModel(reason=message.text))

    await state.update_data(reason=message.text)
    await message.answer(
        escape_markdown(
            text=_(
                '📤 *Post an ad*\n\n💵 Send me the *price* of the ad.\n✍️ e.g. 699.99\n\n🚫 Send /cancel to cancel the operation.'))
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
    categories = await CategoryService.get_categories()
    await state.update_data(categories=categories)
    await show_categories(message, categories, user_language, state, parent_id=None)


@router.message(PostAdStates.MEDIA)
async def post_ad_media(message: Message, state: FSMContext) -> None:
    """
    Get the media content (photos/videos) for the ad.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """

    if (message.content_type == 'photo' and message.photo[-1].file_size > 45 * 1024 * 1024) or \
            (message.content_type == 'video' and message.video.file_size > 45 * 1024 * 1024) or \
            (message.content_type == 'document' and message.document.file_size > 45 * 1024 * 1024):
        await message.answer(escape_markdown(text=_('🚫 The file size must be less than 45 MB.')))
        return

    data = await state.get_data()
    media = data.get('media', [])

    # Check if the user has uploaded 10 or more media files
    if len(media) >= 10:
        await message.answer(escape_markdown(text=_('🚫 You can only upload up to 10 media files.')))
        await state.set_state(PostAdStates.LOCATION)
        await message.answer(escape_markdown(text=_('📍 Send me the *location* of the ad or type it manually.')),
                             reply_markup=InlineKeyboardMarkup(
                                 inline_keyboard=[
                                     [InlineKeyboardButton(text=_('📍 Share Location'), request_location=True)]]
                             ))
        return

    # Handle different media types and add them to the media list
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        media.append({'type': 'photo', 'file_id': file_id})
    elif message.content_type == 'video':
        file_id = message.video.file_id
        media.append({'type': 'video', 'file_id': file_id})
    elif message.content_type == 'document':
        file_id = message.document.file_id
        if message.document.mime_type.startswith('image/'):
            media.append({'type': 'photo', 'file_id': file_id})
        elif message.document.mime_type.startswith('video/'):
            media.append({'type': 'video', 'file_id': file_id})
        else:
            await message.answer(escape_markdown(text=_('🚫 Unsupported document type.')))
    else:
        await message.answer(escape_markdown(text=_('🚫 Unsupported media type.')))
        return

    # Update state data with new media list
    await state.update_data(media=media)

    # Save media (this can be done async)
    await save_media(message, message.bot)

    # Send a message to user asking if they want to upload more media or finish
    await message.answer(
        escape_markdown(text=_('📤 File uploaded. Do you want to add another media file?')),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=_('➕ Add more'), callback_data=AddMediaCallback().pack())],
                [InlineKeyboardButton(text=_('✅ Finish'), callback_data=FinishUploadMediaCallback().pack())]
            ]
        )
    )


@router.callback_query(AddMediaCallback.filter())
async def add_media_action(callback_query, state: FSMContext):
    """
    Add media action.

    :param callback_query: CallbackQuery object
    :param state: FSMContext object
    :return: None
    """

    await callback_query.message.answer(
        escape_markdown(text=_('📤 Send the next media file (photo, video, document).'))
    )
    await state.set_state(PostAdStates.MEDIA)
    await callback_query.answer()


@router.callback_query(FinishUploadMediaCallback.filter())
async def finish_upload_media_action(callback_query, state: FSMContext):
    """
    Finish upload media action.

    :param callback_query: CallbackQuery object
    :param state: FSMContext object
    :return: None
    """

    location_button = KeyboardButton(text=_('📍 Share Location'), request_location=True)
    keyboard = ReplyKeyboardMarkup(keyboard=[[location_button]], resize_keyboard=True)

    await callback_query.message.answer(
        escape_markdown(text=_('📍 Send the *location* of the ad or type it manually.')),
        reply_markup=keyboard
    )
    await state.set_state(PostAdStates.LOCATION)
    await callback_query.answer()


@router.message(PostAdStates.LOCATION, F.content_type == 'location')
async def post_ad_location(message: Message, state: FSMContext) -> None:
    """
    Get the location of the ad via location sharing.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    location = message.location

    await state.update_data(location=location)
    await message.answer(
        escape_markdown(text=_('📤 *Post an ad*\n\n📎 Send me the *contact information* of the ad.')),
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(PostAdStates.CONTACT_INFO)


@router.message(PostAdStates.LOCATION, F.text)
async def post_ad_location_text(message: Message, state: FSMContext) -> None:
    """
    Get the location of the ad via text input.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    location_text = message.text

    await state.update_data(location=location_text)
    await message.answer(
        escape_markdown(text=_('📤 *Post an ad*\n\n📎 Send me the *contact information* of the ad.')),
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(PostAdStates.CONTACT_INFO)


@router.message(PostAdStates.CONTACT_INFO)
async def post_ad_contact_info(message: Message, state: FSMContext) -> None:
    """
    Get the contact information of the ad.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    contact_info = message.text

    # Send /done command to finish the post-ad operation
    await state.update_data(contact_info=contact_info)
    await message.answer(escape_markdown(text=_('📤 *Post an ad*\n\n👍 *Done!*')))
    await finish_post_ad(message, state)


async def finish_post_ad(message: Message, state: FSMContext) -> None:
    """
    Finish the post-ad operation and show the filled form.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    data = await state.get_data()
    title = data['title']
    description = data['description']
    reason = data['reason']
    price = data['price']
    selected_category = data['selected_category']
    media = data['media']
    contact_info = data['contact_info']
    location = data['location']

    # Load the media files
    media_files = await prepare_media_files(media)

    # Get all parent categories based on the path
    category_ids = selected_category['path'].split('.')
    parent_category_translations = []
    for category_id in category_ids:
        category = await CategoryService.get_category_by_id(int(category_id))
        parent_category_translations.extend(category['translations'])

    # Generate hashtags based on the parent categories
    hashtags = [f"#{translation['name'].replace(' ', '_').replace('_&', '')}" for translation in
                parent_category_translations]
    hashtags_text = " ".join(hashtags)

    if isinstance(location, Location) and location.latitude and location.longitude:
        city, county, country = await get_location_info(location.latitude, location.longitude)
        location = f"{city}, {county}, {country}" if city and county and country else _("Unknown location")
    else:
        location = location if isinstance(location, str) else _("Unknown location")

    # Show the filled form
    ad_text = (
        f"*Title:* {title}\n"
        f"*Description:* {description}\n"
        f"*Reason for Selling:* {reason}\n"
        f"*Price:* {price}\n\n"
        f"*Contact Information:* {contact_info}\n"
        f"*Location:* {location}\n\n"
        f"{hashtags_text}"
    )

    media_group = MediaGroupBuilder(caption=escape_markdown(ad_text))

    for media_file in media_files:
        file_path = media_file['file']
        media_type = media_file['type']

        if media_type == 'photo':
            media_group.add_photo(media=file_path)
        elif media_type == 'video':
            media_group.add_video(media=file_path)

    # Send the media group if there are photos/videos, otherwise send the text
    if media_group is not None:
        try:
            await message.answer_media_group(media=media_group.build())
        except Exception as e:
            logger.error(f"Error sending media group: {e}")
            await message.answer(escape_markdown(text=ad_text))
    else:
        await message.answer(escape_markdown(text=ad_text))


async def save_media(message: Message, bot: Bot, media_folder="storage/media"):
    """
    Save the media content (photos/videos) to the media folder with compression.

    :param message: Message object
    :param bot: Bot object
    :param media_folder: The media folder path
    :return: None
    """
    os.makedirs(f"{media_folder}/images", exist_ok=True)
    os.makedirs(f"{media_folder}/video", exist_ok=True)
    os.makedirs(f"{media_folder}/documents", exist_ok=True)

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        file_path = f"{media_folder}/images/{file_id}.jpg"
        await bot.download_file(file.file_path, file_path)
        compress_image(file_path, file_path)

    elif message.content_type == "video":
        file_id = message.video.file_id
        file = await bot.get_file(file_id)
        file_path = f"{media_folder}/video/{file_id}.mp4"
        await bot.download_file(file.file_path, file_path)

        await message.answer(escape_markdown(_("📤 Video is being uploaded to the server...")))
        await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
        compress_video(file_path, file_path)
        await message.answer(escape_markdown(_("✅ Video has been successfully uploaded to the server.")))


    elif message.content_type == "document":
        file_id = message.document.file_id
        file = await bot.get_file(file_id)
        file_extension = os.path.splitext(file.file_path)[1].lower()
        file_path = None
        if file_extension in [".jpg", ".jpeg", ".png"]:
            file_path = f"{media_folder}/images/{file_id}.jpg"
        elif file_extension in [".mp4", ".mov", ".avi"]:
            file_path = f"{media_folder}/video/{file_id}.mp4"
        await bot.download_file(file.file_path, file_path)

        # Compress the image or video
        if file_extension in [".jpg", ".jpeg", ".png"]:
            compress_image(file_path, file_path)
        elif file_extension in [".mp4", ".mov", ".avi"]:
            await message.answer(escape_markdown(_("📤 Video is being uploaded to the server...")))
            await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
            compress_video(file_path, file_path)
            await message.answer(escape_markdown(_("✅ Video has been successfully uploaded to the server.")))
        else:
            await message.answer(escape_markdown(_("🚫 Unsupported file type.")))


def compress_image(input_path, output_path, max_size=(1920, 1080)):
    """
    Compress and resize the image with Pillow.

    :param input_path: Input image file path
    :param output_path: Output image file path
    :param max_size: Maximum resolution
    :return: None
    """
    with Image.open(input_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(output_path, "JPEG")


def preprocess_video(input_path, output_path):
    """
    Preprocess the video with OpenCV.
    Without this step, the video will have a problem with the resampling.

    :param input_path: Input video file path
    :param output_path: Output video file path
    :return: None
    """
    cap = cv2.VideoCapture(input_path)
    fourcc = cv2.VideoWriter.fourcc(*'XVID')
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    cap.release()
    out.release()


def compress_video(input_path, output_path, bitrate="2000k"):
    """
    Compress and resize the video with MoviePy.

    Because of the resampling issue with moviepy, we use opencv-python for video processing.
    Remember to install opencv-python: `pip install opencv-python`.

    :param input_path: Input video file path
    :param output_path: Output video file path
    :param bitrate: Bitrate
    :return: None
    """
    preprocess_video(input_path, "temp_video.mp4")
    with VideoFileClip("temp_video.mp4") as clip:
        clip.write_videofile(output_path, bitrate=bitrate, codec="libx264", audio_codec="aac", preset="slow",
                             temp_audiofile="temp-audio.m4a", remove_temp=True)


async def load_media(file_path):
    """
    Load the media content (photos/videos) from the media folder.

    :param file_path: The path of the media files
    :return: The media file as FSInputFile
    """
    return FSInputFile(file_path)


async def get_location_info(latitude, longitude):
    """
    Get the location information based on the latitude and longitude from the geolocation API.

    :param latitude: Latitude
    :param longitude: Longitude
    :return: City, County, Country
    """
    geolocator = Nominatim(user_agent="advertisement_bot")

    # Get the location information
    location = geolocator.reverse((latitude, longitude))

    if location:
        address = location.raw.get('address', {})

        city = address.get('city', '')
        county = address.get('county', '')
        country = address.get('country', '')

        return city, county, country
    else:
        return None, None, None


async def prepare_media_files(media: list) -> list:
    """
    Check the media files and prepare them for the advertisement.

    :param media: Media files list
    :return: Prepared media files with their types
    """
    media_files = []

    for item in media:
        if item['type'] == 'photo':
            media_path = f"storage/media/images/{item['file_id']}.jpg"
        elif item['type'] == 'video':
            media_path = f"storage/media/video/{item['file_id']}.mp4"
        else:
            continue

        media_file = await load_media(media_path)
        media_files.append({'file': media_file, 'type': item['type']})

    return media_files
