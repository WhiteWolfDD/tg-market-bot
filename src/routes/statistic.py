from aiogram import Router
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from src.services.statistic import StatisticService
from src.utils.helpers import escape_markdown

router = Router()


async def display_statistics(message: Message):
    statistics = await StatisticService.get_full_statistics()

    popular_categories = statistics.get('popular_categories', [])
    if popular_categories is None:
        popular_categories = []

    popular_categories_text = ''
    for idx, category in enumerate(popular_categories, 1):
        popular_categories_text += f"{idx}. {category.get('emoji', '')} {category.get('category_name', 'Unknown')} - {category.get('ad_count', 0)} ads\n"

    msg = _(
        "📊 *Bot Statistics:*\n\n"
        "👥 Total users: {total_users}\n"
        "🆕 New users today: {new_users_today}\n"
        "🟢 Active users: {active_users}\n"
        "\n"
        "📄 Total advertisements: {total_advertisements}\n"
        "📈 Active advertisements: {active_advertisements}\n"
        "✅ Approved advertisements: {successful_advertisements}\n"
        "❌ Deleted advertisements: {deleted_advertisements}\n"
        "\n"
        "📁 Total categories: {total_categories}\n"
        "🔥 Popular categories:\n{popular_categories_text}\n"
        "⏱ Average response time: {response_time_avg:.2f} seconds\n"
    ).format(
        total_users=statistics.get('total_users', 0),
        new_users_today=statistics.get('new_users_today', 0),
        active_users=statistics.get('active_users', 0),
        total_advertisements=statistics.get('total_advertisements', 0),
        active_advertisements=statistics.get('active_advertisements', 0),
        successful_advertisements=statistics.get('successful_advertisements', 0),
        deleted_advertisements=statistics.get('deleted_advertisements', 0),
        total_categories=statistics.get('total_categories', 0),
        popular_categories_text=popular_categories_text,
        response_time_avg=statistics.get('response_time_avg', 0)
    )

    await message.answer(
        text=escape_markdown(msg)
    )
