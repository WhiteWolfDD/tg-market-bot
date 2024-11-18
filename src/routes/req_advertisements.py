from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _

from src.callbacks.admin import ModerateAdCallback, ApproveAdCallback, RejectAdCallback, ManageAdAdminCallback, \
    RenderRequestedAdsCallback
from src.callbacks.advertisement import BackToAdsCallback, EditAdCallback, DeleteAdCallback
from src.callbacks.pagination import ModeratePaginationCallback
from src.services.advertisement import AdvertisementService
from src.utils.helpers import escape_markdown, build_inline_keyboard, build_media_group
from src.utils.log import setup_logging
from src.utils.states import EditAdStates

router = Router()
logger = setup_logging()


@router.callback_query(RenderRequestedAdsCallback().filter())
async def render_requested_ads(target: Message | CallbackQuery, page: int = 1) -> None:
    """
    Render requested advertisements with pagination.

    :param target: Message or CallbackQuery
    :param page: Current page number
    :return:
    """

    ads = await AdvertisementService.get_requested_ads()
    total_pages = (len(ads) + 10 - 1) // 10

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * 10
    end = start + 10
    current_ads = ads[start:end]

    msg = '📜 *Requested advertisements*.\n\nSelect an advertisement to moderate.'

    kbd = build_inline_keyboard(
        keyboard={
            'inline_kbd': [
                [
                    {'text': ad.title, 'callback_data': ModerateAdCallback(ad_id=ad.id).pack()} for ad in current_ads
                ]
            ]
        },
        prev_page_cb=ModeratePaginationCallback(page=page - 1).pack() if page > 1 else None,
        next_page_cb=ModeratePaginationCallback(page=page + 1).pack() if page < total_pages else None
    )

    if isinstance(target, Message):
        await target.answer(text=escape_markdown(msg), reply_markup=kbd.as_markup())
    else:
        await target.message.edit_text(text=escape_markdown(msg), reply_markup=kbd.as_markup())


@router.callback_query(ModerateAdCallback().filter())
async def moderate_ad_handler(callback_query: CallbackQuery, callback_data: ModerateAdCallback):
    ad_id = callback_data.ad_id
    back = bool(callback_data.back)
    advertisement = await AdvertisementService.get_advertisement_by_id(ad_id)

    if not advertisement:
        await callback_query.answer(_('❌ Advertisement not found.'), show_alert=True)
        return

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

    kbd = build_inline_keyboard(
        keyboard={
            'inline_kbd': [
                [
                    {'text': _('✅ Approve'), 'callback_data': ApproveAdCallback(ad_id=ad_id).pack()},
                    {'text': _('🔧 Manage'), 'callback_data': ManageAdAdminCallback(ad_id=ad_id).pack()},
                    {'text': _('❌ Reject'), 'callback_data': RejectAdCallback(ad_id=ad_id).pack()}
                ]
            ]
        },
        back_cb=RenderRequestedAdsCallback().pack()
    )

    action_text = _('🎟 Please choose an action for this ad:')

    if not back:
        try:
            media_group = await build_media_group(ad_id, ad_text)
            await callback_query.message.answer_media_group(media=media_group.build())
        except Exception as e:
            logger.error(f"Failed to send media group: {e}")
            await callback_query.message.answer(escape_markdown(ad_text))

        await callback_query.message.answer(escape_markdown(action_text), reply_markup=kbd.as_markup())
    else:
        await callback_query.message.edit_text(escape_markdown(action_text), reply_markup=kbd.as_markup())

    await callback_query.answer()


@router.callback_query(ManageAdAdminCallback().filter())
async def manage_ad_admin_handler(callback_query: CallbackQuery, state: FSMContext):
    data_parts = callback_query.data.split(':')
    if len(data_parts) != 2:
        await callback_query.answer(_('❌ Invalid callback data.'), show_alert=True)
        return

    action, ad_id_str = data_parts
    try:
        ad_id = int(ad_id_str)
    except ValueError:
        await callback_query.answer(_('❌ Invalid advertisement ID.'), show_alert=True)
        return

    await state.set_state(EditAdStates.MANAGE_AD)
    await state.update_data(ad_id=ad_id)

    msg = _('🔧 What would you like to do with this advertisement?')

    kbd = build_inline_keyboard(
        keyboard={
            'inline_kbd': [
                [
                    {'text': _('✏️ Edit'), 'callback_data': EditAdCallback(ad_id=ad_id, admin=True).pack()},
                    {'text': _('❌ Delete'), 'callback_data': DeleteAdCallback(ad_id=ad_id).pack()}
                ]
            ]
        },
        back_cb=ModerateAdCallback(ad_id=ad_id, back=True).pack()
    )

    await callback_query.message.edit_text(
        escape_markdown(msg),
        reply_markup=kbd.as_markup()
    )
    await callback_query.answer()


