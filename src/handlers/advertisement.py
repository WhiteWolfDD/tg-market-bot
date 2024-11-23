import os
from typing import cast, List, Union

from aiogram import Router, Bot
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, KeyboardButton, \
    ReplyKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from src.callbacks.admin import RejectAdCallback, ApproveAdCallback, ManageAdAdminCallback
from src.callbacks.advertisement import AddMediaCallback, FinishUploadMediaCallback, DeleteAdCallback, EditAdCallback, \
    BackToAdsCallback, ManageAdCallback
from src.services.advertisement import AdvertisementService
from src.utils.const import AdvertisementConfig, StoragePaths
from src.utils.helpers import escape_markdown, build_media_group, build_inline_keyboard
from src.utils.log import setup_logging
from src.utils.states import PostAdStates, EditAdStates

router = Router()
logger = setup_logging()


async def handle_media_upload(message: Message, state: FSMContext):
    max_file_size = AdvertisementConfig.MAX_FILE_SIZE
    file_size, file_id, media_type = await get_media_info(message)

    if not all([file_size, file_id, media_type]):
        await message.answer(escape_markdown(_('🚫 Unsupported media type.')))
        return

    if file_size > max_file_size:
        await message.answer(escape_markdown(_('🚫 The file size must be less than 45 MB.')))
        return

    data = await state.get_data()
    media = data.get('media', [])

    if len(media) >= 10:
        await message.answer(escape_markdown(
            text=_('🚫 You can only upload up to 10 media files.')),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=_('✅ Finish'),
                                      callback_data=FinishUploadMediaCallback().pack())]
            ])
        )

    media.append({'type': media_type, 'file_id': file_id})
    await state.update_data(media=media)

    await save_media(message, message.bot)

    await message.answer(
        escape_markdown(_('📤 File uploaded. Do you want to add another media file?')),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('➕ Add more'),
                                  callback_data=AddMediaCallback().pack())],
            [InlineKeyboardButton(text=_('✅ Finish'),
                                  callback_data=FinishUploadMediaCallback().pack())]
        ])
    )


@router.callback_query(AddMediaCallback.filter())
async def add_media_action(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        await callback_query.answer(_('🚫 Invalid state.'))
        return

    if current_state.startswith('PostAdStates'):
        await state.set_state(PostAdStates.MEDIA)
    elif current_state.startswith('EditAdStates'):
        await state.set_state(EditAdStates.MEDIA)
    else:
        await callback_query.answer(_('🚫 Invalid state.'))
        return

    await callback_query.message.answer(
        escape_markdown(_('📤 Send the next media file (photo, video, document).'))
    )
    await callback_query.answer()


@router.callback_query(FinishUploadMediaCallback.filter())
async def finish_upload_media_action(callback_query: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        await callback_query.answer(_('🚫 Invalid state.'))
        return

    if current_state.startswith('PostAdStates'):
        await proceed_to_location_state(callback_query.message, state)
    elif current_state.startswith('EditAdStates'):
        data = await state.get_data()
        ad_id = data.get('ad_id')
        media = data.get('media')
        if not media:
            await callback_query.answer(_('🚫 No media files found.'))
            return
        await AdvertisementService.update_advertisement_media(ad_id, media=media)
        await callback_query.message.answer(escape_markdown(_('✅ Media files have been successfully updated.')))
        await manage_ad(callback_query, ad_id)
    else:
        await callback_query.answer(_('🚫 Invalid state.'))
        return

    await callback_query.answer()


async def get_media_info(message: Message):
    """
    Get media file information.

    :param message: Message object
    :return: Tuple
    """
    if message.content_type == 'photo':
        file = message.photo[-1]
        media_type = 'photo'
    elif message.content_type == 'video':
        file = message.video
        media_type = 'video'
    elif message.content_type == 'document':
        file = message.document
        mime_type = file.mime_type
        if mime_type.startswith('image/'):
            media_type = 'photo'
        elif mime_type.startswith('video/'):
            media_type = 'video'
        else:
            return None, None, None
    else:
        return None, None, None

    return file.file_size, file.file_id, media_type


async def proceed_to_location_state(message: Message, state: FSMContext):
    """
    Proceed to the location state.

    :param message: Message object
    :param state: FSMContext object
    :return: None
    """
    location_button = KeyboardButton(text=_('📍 Share Location'), request_location=True)
    keyboard = ReplyKeyboardMarkup(keyboard=[[location_button]], resize_keyboard=True)

    await state.set_state(PostAdStates.LOCATION)
    await message.answer(
        escape_markdown(_('📍 Send me the *location* of the ad or type it manually.')),
        reply_markup=keyboard
    )


async def save_media(message: Message, bot: Bot):
    """
    Save the media file to the server storage.

    :param message: Message object
    :param bot: Bot object
    :return: None
    """
    os.makedirs(StoragePaths.PHOTO_PATH, exist_ok=True)
    os.makedirs(StoragePaths.VIDEO_PATH, exist_ok=True)

    file_size, file_id, media_type = await get_media_info(message)
    if not all([file_size, file_id, media_type]):
        return

    if media_type == 'photo':
        file_path = os.path.join(StoragePaths.PHOTO_PATH, f"{file_id}.jpg")
    elif media_type == 'video':
        file_path = os.path.join(StoragePaths.VIDEO_PATH, f"{file_id}.mp4")
        await message.answer(escape_markdown(_("📤 Video is being uploaded to the server...")))
        await bot.send_chat_action(message.chat.id, ChatAction.UPLOAD_VIDEO)
    else:
        return

    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, file_path)
    if media_type == 'video':
        await message.answer(escape_markdown(_("✅ Video has been successfully uploaded to the server.")))


@router.callback_query(ManageAdCallback().filter())
async def manage_ad(update: Union[CallbackQuery, Message], ad_id: int = None):
    if not ad_id:
        ad_id = int(update.data.split(':')[1])
    ad = await AdvertisementService.get_advertisement_by_id(ad_id)

    hashtags = " ".join(cast(List[str], ad.hashtags))
    ad_text = (
        f"*Title:* {ad.title}\n"
        f"*Description:* {ad.description}\n"
        f"*Reason for Selling:* {ad.reason}\n"
        f"*Price:* {ad.price} €\n"
        f"*Contact Information:* {ad.contact_info}\n"
        f"*Location:* {ad.location}\n"
        f"{hashtags}"
    )

    media_group = await build_media_group(ad.id, ad_text)

    try:
        if isinstance(update, CallbackQuery):
            await update.message.answer_media_group(media=media_group.build())
        else:
            await update.answer_media_group(media=media_group.build())
    except Exception as e:
        logger.error(f"Failed to send media group: {e}")
        if isinstance(update, CallbackQuery):
            await update.message.answer(escape_markdown(ad_text))
        else:
            await update.answer(escape_markdown(ad_text))

    kbd = build_inline_keyboard(
        keyboard={'inline_kbd': [
            [{'text': _('🗑 Delete'), 'callback_data': DeleteAdCallback(ad_id=cast(int, ad.id)).pack()}],
            [{'text': _('✏️ Edit'), 'callback_data': EditAdCallback(ad_id=cast(int, ad.id)).pack()}] if ad.status == 'pending' else [],
        ]},
        back_cb=BackToAdsCallback().pack()
    )

    if isinstance(update, CallbackQuery):
        await update.message.answer(
            text=escape_markdown(_('🎟 Please manage this ad:')),
            reply_markup=kbd.as_markup()
        )
    else:
        await update.answer(
            text=escape_markdown(_('🎟 Please manage this ad:')),
            reply_markup=kbd.as_markup()
        )
