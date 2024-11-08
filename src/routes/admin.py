from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.routes.category import show_categories
from src.routes.exception_logs import render_exception_logs
from src.routes.statistic import display_statistics
from src.service.category import CategoryService


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

    pass
