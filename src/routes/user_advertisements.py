from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from src.callbacks.advertisement import (ShowApprovedAdsCallback, ShowPendingAdsCallback, ShowRejectedAdsCallback,
                                         BackToAdsCallback, ManageAdCallback, PaginateAdsCallback, DeleteAdCallback,
                                         EditAdCallback)
from src.callbacks.main import DeleteMessageCallback
from src.routes.edit_advertisement import edit_advertisement
from src.services.advertisement import AdvertisementService
from src.services.user import UserService
from src.utils.helpers import escape_markdown, build_inline_keyboard
from src.utils.log import setup_logging

router = Router()
logger = setup_logging()


@router.message(F.text == __('📦 My ads'))
async def show_user_advertisements(message: Message) -> None:
    """
    Show user advertisements.
    """
    await display_user_ads(message)


@router.callback_query(ShowApprovedAdsCallback().filter())
async def show_approved_ads(callback_query: CallbackQuery) -> None:
    await show_ads_by_status(callback_query, 'approved')


@router.callback_query(ShowPendingAdsCallback().filter())
async def show_pending_ads(callback_query: CallbackQuery) -> None:
    await show_ads_by_status(callback_query, 'pending')


@router.callback_query(ShowRejectedAdsCallback().filter())
async def show_rejected_ads(callback_query: CallbackQuery) -> None:
    await show_ads_by_status(callback_query, 'rejected')


@router.callback_query(BackToAdsCallback().filter())
async def back_to_ads(callback_query: CallbackQuery) -> None:
    await display_user_ads(callback_query.message)


async def display_user_ads(target: Message) -> None:
    user_id = await UserService.get_user_id_by_telegram_id(
        target.chat.id if target.chat else target.from_user.id
    )
    ads = await AdvertisementService.get_advertisements_by_owner_id(user_id)

    approved_count = sum(1 for ad in ads if ad.status == 'approved')
    pending_count = sum(1 for ad in ads if ad.status == 'pending')
    rejected_count = sum(1 for ad in ads if ad.status == 'rejected')

    msg = _('📦 *Your ads*.\n\nSelect a category to view your ads.')

    client_msg = await target.bot.send_message(
        chat_id=target.chat.id,
        text=escape_markdown(msg)
    )

    kbd = {
        'inline_kbd': [
            [{'text': f"{_('🟢 Approved ads')} ({approved_count})", 'callback_data': ShowApprovedAdsCallback().pack()}],
            [{'text': f"{_('🟡 Pending ads')} ({pending_count})", 'callback_data': ShowPendingAdsCallback().pack()}],
            [{'text': f"{_('🔴 Rejected ads')} ({rejected_count})", 'callback_data': ShowRejectedAdsCallback().pack()}],
            [{'text': '🚫 Cancel', 'callback_data': DeleteMessageCallback(message_id=client_msg.message_id).pack()}]
        ]
    }

    await target.bot.edit_message_reply_markup(
        chat_id=client_msg.chat.id,
        message_id=client_msg.message_id,
        reply_markup=build_inline_keyboard(keyboard=kbd).as_markup()
    )


async def show_ads_by_status(callback_query: CallbackQuery, status: str, page: int = 1) -> None:
    user_id = await UserService.get_user_id_by_telegram_id(callback_query.from_user.id)
    ads = await AdvertisementService.get_advertisements_by_owner_id(user_id)
    filtered_ads = [ad for ad in ads if ad.status == status]

    if not filtered_ads:
        await callback_query.message.edit_text(
            escape_markdown(_('🫢 No ads found in this category.')),
            reply_markup=build_inline_keyboard(
                keyboard={'inline_kbd': [[{'text': _('Back'), 'callback_data': BackToAdsCallback().pack()}]]}
            ).as_markup()
        )
        return

    total_pages = (len(filtered_ads) + 9 - 1) // 9
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * 9
    end = start + 9
    current_ads = filtered_ads[start:end]

    msg = _('📦 *Your ads*.\n\nSelect an advertisement to manage.')
    kbd = build_inline_keyboard(
        keyboard={'inline_kbd': [
            [{'text': ad.title, 'callback_data': ManageAdCallback(ad_id=ad.id).pack()} for ad in current_ads[i:i + 3]]
            for i in range(0, len(current_ads), 3)
        ]},
        back_cb=BackToAdsCallback().pack(),
        prev_page_cb=PaginateAdsCallback(status=status, page=page - 1).pack() if page > 1 else None,
        next_page_cb=PaginateAdsCallback(status=status, page=page + 1).pack() if page < total_pages else None
    )

    await callback_query.message.edit_text(
        text=escape_markdown(msg),
        reply_markup=kbd.as_markup()
    )


@router.callback_query(F.data.startswith('paginate_ads:'))
async def paginate_ads(callback_query: CallbackQuery) -> None:
    _, status, page = callback_query.data.split(':')
    await show_ads_by_status(callback_query, status, int(page))


@router.callback_query(DeleteAdCallback().filter())
async def delete_ad(callback_query: CallbackQuery) -> None:
    ad_id = int(callback_query.data.split(':')[1])

    # Delete ad from a channel if it's approved
    ad = await AdvertisementService.get_advertisement_by_id(ad_id)
    if ad.status == 'approved':
        await AdvertisementService.delete_advertisement_from_channel(
            bot=callback_query.bot,
            advertisement_id=ad_id
        )

    await AdvertisementService.delete_advertisement(ad_id)
    await callback_query.answer(_('Ad deleted.'))
    await back_to_ads(callback_query)


@router.callback_query(EditAdCallback().filter())
async def edit_ad(callback_query: CallbackQuery) -> None:
    ad_id = int(callback_query.data.split(':')[1])
    admin = bool(callback_query.data.split(':')[2])

    await edit_advertisement(callback_query, ad_id, admin)
