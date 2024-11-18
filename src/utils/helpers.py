import os
import re

from aiogram.types import InlineKeyboardButton, FSInputFile, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from aiogram.utils.media_group import MediaGroupBuilder
from sqlalchemy.orm import Mapped

from src.callbacks.advertisement import EditAdFieldCallback
from src.callbacks.main import HomeCallback
from src.services.advertisement import AdvertisementService
from src.utils.const import StoragePaths


def escape_markdown(text: str) -> str:
    """
    Escape markdown characters.
    :param text: The text to escape.
    :return: The escaped text.
    """

    reserved_chars = r'_[]()~>#\+\-=|{}.!'
    return re.sub(f'([{re.escape(reserved_chars)}])', r'\\\1', text)


def build_inline_keyboard(
        keyboard: dict,
        back_cb: str = None,
        home_button: bool = False,
        custom_home_cb: str = None,
        prev_page_cb: str = None,
        next_page_cb: str = None,
        first_page_cb: str = None,
        last_page_cb: str = None,
        request_location: bool = False
) -> InlineKeyboardBuilder:
    """
    Build an inline keyboard.
    """
    builder = InlineKeyboardBuilder(
        [
            [
                InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button['callback_data'] if 'callback_data' in button else None,
                    url=button['url'] if 'url' in button else None,
                    request_location=request_location
                ) for button in row if button
            ] for row in keyboard['inline_kbd']
        ]
    )

    if prev_page_cb and next_page_cb:
        buttons = [
            InlineKeyboardButton(
                text='⏮',
                callback_data=first_page_cb
            ) if first_page_cb else None,
            InlineKeyboardButton(
                text=_('⬅️ Prev'),
                callback_data=prev_page_cb
            ),
            InlineKeyboardButton(
                text=_('Next ➡️'),
                callback_data=next_page_cb
            ),
            InlineKeyboardButton(
                text='⏭',
                callback_data=last_page_cb
            ) if last_page_cb else None
        ]

        buttons = [button for button in buttons if button]
        builder.row(*buttons)

    if back_cb:
        builder.row(
            InlineKeyboardButton(
                text=_('⬅️ Back'),
                callback_data=back_cb
            )
        )

    if home_button:
        builder.row(
            InlineKeyboardButton(
                text=_('🏠 Home'),
                callback_data=HomeCallback().pack() if not custom_home_cb else custom_home_cb
            )
        )

    return builder


async def build_media_group(advertisement_id: int | Mapped[int], ad_text: str) -> MediaGroupBuilder:
    """
    Build a media group.
    """
    media_files = await AdvertisementService.get_media_files(advertisement_id)
    media_group = MediaGroupBuilder(caption=escape_markdown(ad_text))

    for media in media_files:
        if media.media_type == 'video':
            file_path = os.path.join(StoragePaths.VIDEO_PATH, f"{media.file_id}.mp4")
            media_file = FSInputFile(file_path)
            media_group.add_video(media=media_file)
        else:
            file_path = os.path.join(StoragePaths.PHOTO_PATH, f"{media.file_id}.jpg")
            media_file = FSInputFile(file_path)
            media_group.add_photo(media=media_file)

    return media_group


def build_edit_ad_keyboard(advertisement_id: int) -> dict:
    return {
        'inline_kbd': [
            [{'text': _('📷 Media'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='media').pack()}],
            [{'text': _('📝 Title'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='title').pack()}],
            [{'text': _('📄 Description'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='description').pack()}],
            [{'text': _('💡 Reason for Selling'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='reason').pack()}],
            [{'text': _('💰 Price'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='price').pack()}],
            [{'text': _('📞 Contact Information'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='contact_info').pack()}],
            [{'text': _('📍 Location'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='location').pack()}],
            [{'text': _('🏷️ Hashtags'),
              'callback_data': EditAdFieldCallback(ad_id=advertisement_id, field='hashtags').pack()}]
        ]
    }