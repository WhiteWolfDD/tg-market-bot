from aiogram import Router
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from src.services.statistic import StatisticService
from src.utils.helpers import escape_markdown

router = Router()


async def display_statistics(message: Message):
    statistics = await StatisticService.get_full_statistics()

    popular_categories = statistics.get('popular_categories', [])
    popular_categories_text = ''
    for idx, category in enumerate(popular_categories, 1):
        popular_categories_text += f"{idx}. {category.get('emoji', '')} {category.get('category_name', 'Unknown')} - {category.get('ad_count', 0)} ads\n"

    msg = _(
        f"📊 *Bot Statistics:*\n\n"
        f"👥 Total users: {statistics.get('total_users', 0)}\n"
        f"🆕 New users today: {statistics.get('new_users_today', 0)}\n"
        f"🟢 Active users: {statistics.get('active_users', 0)}\n"
        f"\n"
        f"📄 Total advertisements: {statistics.get('total_advertisements', 0)}\n"
        f"📈 Active advertisements: {statistics.get('active_advertisements', 0)}\n"
        f"✅ Approved advertisements: {statistics.get('successful_advertisements', 0)}\n"
        f"❌ Deleted advertisements: {statistics.get('deleted_advertisements', 0)}\n"
        f"\n"
        f"📁 Total categories: {statistics.get('total_categories', 0)}\n"
        f"🔥 Popular categories:\n{popular_categories_text}\n"
        f"⏱ Average response time: {statistics.get('response_time_avg', 0):.2f} seconds\n"
    )

    await message.answer(
        text=escape_markdown(msg)
    )
