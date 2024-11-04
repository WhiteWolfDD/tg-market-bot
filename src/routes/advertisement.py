import os
from decimal import Decimal, InvalidOperation

from PIL import Image
from moviepy.editor import VideoFileClip
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, FSInputFile
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from src.schemas.advertisement import AdvertisementModel, ValidationError, translate_validation_error
from src.routes.category import show_categories
from src.service.category import CategoryService
from src.service.user import UserService
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
    data = await state.get_data()

    media = data.get('media', [])
    media.append({
        'type': message.content_type,
        'file_id': message.photo[-1].file_id if message.content_type == 'photo' else message.video.file_id
    })

    await state.update_data(media=media)

    await save_media(message, message.bot)

    await message.answer(escape_markdown(text=_('📤 *Post an ad*\n\n📍 Send me the *location* of the ad.')))
    await state.set_state(PostAdStates.LOCATION)


@router.message(PostAdStates.LOCATION)
async def post_ad_location(message: Message, state: FSMContext) -> None:
    """
    Get the location of the ad.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    location = message.location

    await state.update_data(location=location)
    await message.answer(escape_markdown(text=_('📤 *Post an ad*\n\n📎 Send me the *contact information* of the ad.')))
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
    price = data['price']
    selected_category = data['selected_category']
    media = data['media'][0]
    contact_info = data['contact_info']
    location = data['location']

    media_path = f"storage/media/{'images' if media['type'] == 'photo' else 'video'}/{media['file_id']}.{'jpg' if media['type'] == 'photo' else 'mp4'}"
    media_file = await load_media(media_path)

    selected_category_translation = selected_category['translations'][0]

    # Get all parent categories based on the path
    category_ids = selected_category['path'].split('.')
    parent_category_translations = []
    for category_id in category_ids:
        category = await CategoryService.get_category_by_id(int(category_id))
        parent_category_translations.extend(category['translations'])

    # Prepare the ad text
    category_text = f"{selected_category_translation['name'].replace(' ', '_').replace('_&', '')}"
    hashtags = [f"#{translation['name'].replace(' ', '_').replace('_&', '')}" for translation in parent_category_translations]
    hashtags_text = " ".join(hashtags)

    ad_text = (
        f"*Title:* {title}\n"
        f"*Description:* {description}\n"
        f"*Price:* {price}\n\n"
        f"*Contact Information:* {contact_info}\n"
        f"*Location:* {location}\n\n"
        f"{hashtags_text} #{category_text}"
    )

    # Show media
    await message.answer_photo(media_file, caption=escape_markdown(
        ad_text)) if media['type'] == 'photo' else await message.answer_video(media_file,
                                                                              caption=escape_markdown(ad_text))
    await state.clear()


def save_compressed_image(file_path, destination_path, quality=85):
    """
    Save a compressed image.

    :param file_path: The path of the image file
    :param destination_path: The path to save the compressed image
    :param quality: The quality of the compressed image
    :return: None
    """
    with Image.open(file_path) as img:
        img = img.convert("RGB")
        img.save(destination_path, "JPEG", quality=quality)


def save_compressed_video(input_path, output_path, target_size=(1280, 720), bitrate="500k"):
    """
    Save a compressed video.

    :param input_path: Input video file path
    :param output_path: Output video file path
    :param target_size: The target size of the video
    :param bitrate: The bitrate of the video
    :return: None
    """
    with VideoFileClip(input_path) as clip:
        clip_resized = clip.resize(newsize=target_size)
        clip_resized.write_videofile(output_path, codec="libx264", bitrate=bitrate, audio_codec="aac")


async def save_media(message: Message, bot: Bot, media_folder="storage/media"):
    """
    Save the media content (photos/videos) to the media folder.

    :param message: Message object
    :param bot: Bot object
    :param media_folder: The media folder path
    :return: None
    """
    os.makedirs(f"{media_folder}/images", exist_ok=True)
    os.makedirs(f"{media_folder}/video", exist_ok=True)

    if message.content_type == "photo":
        file_id = message.photo[-1].file_id
        file = await bot.get_file(file_id)
        file_path = f"{media_folder}/images/{file_id}.jpg"
        await bot.download_file(file.file_path, file_path)
        save_compressed_image(file_path, file_path)

    elif message.content_type == "video":
        file_id = message.video.file_id
        file = await bot.get_file(file_id)
        file_path = f"{media_folder}/video/{file_id}.mp4"
        await bot.download_file(file.file_path, file_path)
        save_compressed_video(file_path, file_path)


async def load_media(file_path):
    """
    Load the media content (photos/videos) from the media folder.

    :param file_path: The path of the media file
    :return: The media file as FSInputFile
    """
    return FSInputFile(file_path)
