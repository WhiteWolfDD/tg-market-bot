import os

from aiogram import Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from src.callbacks.admin import ApproveAdCallback, RejectAdCallback
from src.routes.category import show_categories
from src.routes.exception_logs import render_exception_logs
from src.routes.req_advertisements import render_requested_ads
from src.routes.statistic import display_statistics
from src.services.advertisement import AdvertisementService
from src.services.category import CategoryService
from src.services.user import UserService
from src.utils.helpers import escape_markdown, build_media_group
from src.utils.log import setup_logging

router = Router()
logger = setup_logging()


async def manage_categories(message: Message, state: FSMContext) -> None:
    """
    Category management.
    """

    categories = await CategoryService.get_categories()
    await state.clear()
    await state.update_data(categories=categories)
    user_language = message.from_user.language_code or 'en'
    await show_categories(message, categories, user_language, state, parent_id=None, admin_mode=True)


async def view_statistics(message: Message) -> None:
    """
    View statistics.
    """

    await display_statistics(message)


async def view_exception_logs(message: Message) -> None:
    """
    View exception logs.
    """

    await render_exception_logs(message)


async def view_requested_ads(message: Message) -> None:
    """
    View requested ads.
    """

    await render_requested_ads(message)


@router.callback_query(ApproveAdCallback.filter())
async def handle_approve_ad(callback_query: CallbackQuery, callback_data: ApproveAdCallback):
    ad_id = callback_data.ad_id
    status = 'approved'
    user_message = _('✅ Your ad has been approved and posted in the channel.')
    admin_message = _('✅ Advertisement approved.')

    try:
        await post_ad_to_channel(ad_id, callback_query.bot)

        await update_advertisement_status(callback_query, ad_id, status, user_message, admin_message)
    except Exception as e:
        logger.error(f"Error while posting ad to channel: {e}")
        await callback_query.answer(_('🚫 Error while posting ad to channel.'), show_alert=True)


@router.callback_query(RejectAdCallback.filter())
async def handle_reject_ad(callback_query: CallbackQuery, callback_data: RejectAdCallback):
    ad_id = callback_data.ad_id
    status = 'rejected'
    ad = await AdvertisementService.get_advertisement_by_id(ad_id)
    ad_title = ad.title if ad else __(f'with ID {ad_id}')
    user_message = _(f'❌ Your ad {ad_title} has been rejected. Please correct the mistakes and try again.')
    admin_message = _('❌ Advertisement rejected.')

    await update_advertisement_status(callback_query, ad_id, status, user_message, admin_message)


async def update_advertisement_status(callback_query: CallbackQuery,
                                      ad_id: int, status: str,
                                      user_message: str,
                                      admin_message: str
                                      ):
    await AdvertisementService.update_advertisement_status(ad_id, status)

    owner_id = await AdvertisementService.get_owner_id_by_advertisement_id(ad_id)
    telegram_user_id = await UserService.get_user_telegram_id(owner_id)

    if telegram_user_id is None:
        await callback_query.answer(_('🚫 Cannot find the user.'), show_alert=True)
        return

    await callback_query.bot.send_message(
        chat_id=telegram_user_id,
        text=escape_markdown(user_message)
    )

    await callback_query.answer(admin_message)
    await callback_query.message.delete()


async def post_ad_to_channel(ad_id: int, bot: Bot):
    advertisement = await AdvertisementService.get_advertisement_by_id(ad_id)
    if advertisement is None:
        logger.error(f"Advertisement with ID {ad_id} does not exist.")
        return

    channel_id = os.getenv("CHANNEL_ID")
    if channel_id is None:
        logger.error("CHANNEL_ID does not exist.")
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

    media_group = await build_media_group(ad_id, ad_text)

    try:
        messages = await bot.send_media_group(chat_id=channel_id, media=media_group.build())
        message_ids = [message.message_id for message in messages]
        await AdvertisementService.update_advertisement(advertisement_id=ad_id, channel_message_ids=message_ids)
    except Exception as e:
        logger.error(f"Cant send media group: {e}")
