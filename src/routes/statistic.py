from aiogram import Router
from aiogram.types import Message
from sqlalchemy import select, func
from src.database import get_session
from src.models import User, Advertisement, Category
from src.utils.helpers import escape_markdown

router = Router()


async def collect_statistics():
    """
    Collect bot statistics.
    """

    async with get_session() as session:
        total_users = await session.execute(select(func.count()).select_from(User))
        total_ads = await session.execute(select(func.count()).select_from(Advertisement))
        total_categories = await session.execute(select(func.count()).select_from(Category))
        # total_requests = await session.execute(select(func.count()).select_from(Request))

        return {
            'total_users': total_users.scalar(),
            'total_ads': total_ads.scalar(),
            'total_categories': total_categories.scalar(),
            # 'total_requests': total_requests.scalar()
        }

async def display_statistics(message: Message):
    stats = await collect_statistics()

    msg = (
        f"*📊 Bot Statistics*\n\n"
        f"Total users: {stats['total_users']}\n"
        f"Total ads: {stats['total_ads']}\n"
        f"Total categories: {stats['total_categories']}\n"
        # f"Total requests: {stats['total_requests']}\n"
    )

    await message.answer(
        text=escape_markdown(msg),
        parse_mode='MarkdownV2'
    )

