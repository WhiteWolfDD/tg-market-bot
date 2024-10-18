import asyncio
import os
import math
from typing import List, Dict, Any

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _
from sqlalchemy import select, update

from src.callbacks.category import CategoryCallback
from src.callbacks.pagination import PaginationCallback
from src.callbacks.admin_category_action import AdminCategoryActionCallback
from src.database import get_session
from src.models import Category
from src.utils.helpers import escape_markdown
from src.utils.cache import get_categories, set_categories, get_categories_from_db
from src.utils.log import setup_logging

logger = setup_logging()
router = Router()


def is_admin(user_id: int) -> bool:
    """Checks if the user is an administrator."""
    return str(user_id) == os.getenv('ADMIN_ID')


def get_category_name(category: Dict[str, Any], language_code: str) -> str:
    """Retrieves the category name in the specified language."""
    translations = category['translations']
    category_name = next(
        (t['name'] for t in translations if t['language_code'] == language_code),
        next((t['name'] for t in translations if t['language_code'] == 'en'), None)
    )
    return category_name


async def get_categories_from_state_or_cache(state: FSMContext) -> List[Dict[str, Any]]:
    """Gets categories from state or cache."""
    data = await state.get_data()
    categories = data.get('categories')
    if categories is None:
        categories = await get_categories()
        await state.update_data(categories=categories)
    return categories


async def show_categories(
        message_or_query: Message | CallbackQuery,
        categories: List[Dict[str, Any]],
        user_language: str,
        state: FSMContext,
        parent_id: int = None,
        search_query: str = None,
        admin_mode: bool = False,
        page: int = 1,
        page_size: int = 30
) -> None:
    """Displays categories with navigation and selection (admin and user modes)."""
    logger.debug(f"show_categories called with parent_id={parent_id}, search_query={search_query}, page={page}")

    if not categories:
        await message_or_query.answer(escape_markdown(_("No categories found.")))
        return

    await state.update_data(parent_id=parent_id)

    if search_query:
        filtered_categories = [
            category for category in categories
            if any(
                search_query.lower() in t['name'].lower()
                for t in category['translations']
                if t['language_code'] == user_language
            )
        ]
    else:
        filtered_categories = [
            category for category in categories
            if category['parent_id'] == parent_id
        ]

    total_pages = math.ceil(len(filtered_categories) / page_size)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_categories = filtered_categories[start_index:end_index]

    buttons = []
    for category in paginated_categories:
        category_name = get_category_name(category, user_language)
        status_emoji = "🟢" if category.get('status', True) else "🔴"

        if is_admin(message_or_query.from_user.id) or admin_mode:
            buttons.append([
                InlineKeyboardButton(
                    text=f"{status_emoji} {category['emoji']} {category_name}",
                    callback_data=CategoryCallback(
                        category_id=category['id'],
                        action='navigate',
                        parent_id=category['parent_id']
                    ).pack()
                )
            ])
        else:
            if category.get('status', True):
                buttons.append([
                    InlineKeyboardButton(
                        text=f"{category['emoji']} {category_name}",
                        callback_data=CategoryCallback(
                            category_id=category['id'],
                            action='navigate',
                            parent_id=category['parent_id']
                        ).pack()
                    )
                ])

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(InlineKeyboardButton(
            text=_('⬅️ Back'),
            callback_data=PaginationCallback(page=page - 1).pack()
        ))
    if page < total_pages:
        pagination_buttons.append(InlineKeyboardButton(
            text=_('➡️ Forward'),
            callback_data=PaginationCallback(page=page + 1).pack()
        ))

    buttons.append([
        InlineKeyboardButton(text=_('🔍 Search'), callback_data='search_categories')
    ])

    if pagination_buttons:
        buttons.append(pagination_buttons)

    if is_admin(message_or_query.from_user.id):
        buttons.append([
            InlineKeyboardButton(text=_('❌ Cancel'), callback_data='cancel_action')
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    category_text = escape_markdown(_("Please select a category:"))
    if search_query:
        category_text += f" '{search_query}'"

    if isinstance(message_or_query, Message):
        await message_or_query.answer(
            escape_markdown(text=category_text),
            reply_markup=keyboard
        )
    elif isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(
            escape_markdown(text=category_text),
            reply_markup=keyboard
        )
        await message_or_query.answer()


@router.callback_query(CategoryCallback.filter())
async def navigate_category(callback_query: CallbackQuery, callback_data: CategoryCallback, state: FSMContext) -> None:
    """Handles category navigation and selection (for both users and admins)."""
    logger.debug(f"navigate_category called by user {callback_query.from_user.id} with data {callback_data}")

    categories = await get_categories_from_state_or_cache(state)

    selected_category = next((cat for cat in categories if cat['id'] == callback_data.category_id), None)
    if not selected_category:
        await callback_query.answer(_("Category not found."), show_alert=True)
        return

    if is_admin(callback_query.from_user.id):
        await handle_admin_category_selection(callback_query, selected_category, categories)
    else:
        await handle_user_category_selection(callback_query, selected_category, categories, state)


async def handle_admin_category_selection(
        callback_query: CallbackQuery,
        category: Dict[str, Any],
        categories: List[Dict[str, Any]]
) -> None:
    """Handles category selection by the administrator."""
    child_categories = [cat for cat in categories if cat['parent_id'] == category['id']]
    buttons = []

    if child_categories:
        buttons.append([
            InlineKeyboardButton(
                text=escape_markdown(_('➡️ Go to child categories')),
                callback_data=AdminCategoryActionCallback(
                    category_id=category['id'],
                    action='go_to_children'
                ).pack()
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text=escape_markdown(_('🔄 Toggle category status')),
            callback_data=AdminCategoryActionCallback(
                category_id=category['id'],
                action='toggle_status'
            ).pack()
        )
    ])

    buttons.append([
        InlineKeyboardButton(text=escape_markdown(_('❌ Cancel')), callback_data='cancel_action')
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    category_name = get_category_name(category, callback_query.from_user.language_code or 'en')

    await callback_query.message.edit_text(
        escape_markdown(text=_('You have selected the category: {category_name}\nChoose an action:').format(
            category_name=category_name)),
        reply_markup=keyboard
    )
    await callback_query.answer()


async def handle_user_category_selection(
        callback_query: CallbackQuery,
        category: Dict[str, Any],
        categories: List[Dict[str, Any]],
        state: FSMContext
) -> None:
    """Handles category selection by the user."""
    child_categories = [cat for cat in categories if cat['parent_id'] == category['id'] and cat.get('status', True)]
    if child_categories:
        await show_categories(
            callback_query,
            categories,
            callback_query.from_user.language_code or 'en',
            state,
            parent_id=category['id']
        )
    else:
        await callback_query.answer(_("This is the last category."), show_alert=True)


@router.callback_query(AdminCategoryActionCallback.filter())
async def handle_admin_category_action(callback_query: CallbackQuery, callback_data: AdminCategoryActionCallback,
                                       state: FSMContext) -> None:
    await callback_query.answer()

    if callback_data.action == 'toggle_status':
        # Proceed to toggle status
        # Edit previous message to only one smile that indicates processing
        await callback_query.message.edit_text(escape_markdown(_("⏳ Processing, please wait...\n\n It may take a while.")))
        asyncio.create_task(process_admin_action(callback_query, callback_data, state))
    elif callback_data.action == 'go_to_children':
        # Navigate to child categories
        categories = await get_categories_from_state_or_cache(state)
        user_language = callback_query.from_user.language_code or 'en'
        await show_categories(callback_query, categories, user_language, state, parent_id=callback_data.category_id)
    else:
        await callback_query.answer(_("Unknown action."), show_alert=True)


async def process_admin_action(callback_query: CallbackQuery, callback_data: AdminCategoryActionCallback,
                               state: FSMContext):
    try:
        await toggle_category_and_children_status(callback_data.category_id)
        categories = await get_categories_from_db()
        await state.update_data(categories=categories)

        # Уведомляем администратора о завершении
        await callback_query.message.edit_text(escape_markdown(_("✅ Category status updated.")))

        # Показываем обновлённый список категорий
        user_language = callback_query.from_user.language_code or 'en'
        data = await state.get_data()
        parent_id = data.get('parent_id')
        await show_categories(callback_query.message, categories, user_language, state, parent_id=parent_id, admin_mode=True)
    except Exception as e:
        logger.error(f"Error updating category status: {e}")
        await callback_query.message.answer(escape_markdown(_("An error occurred while updating the category status.")))


@router.callback_query(F.data == 'cancel_action')
async def cancel_last_action(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Handles the cancellation of the last administrator action."""
    logger.debug(f"cancel_last_action called by user {callback_query.from_user.id}")
    await state.clear()
    await callback_query.answer(_("Action canceled."))
    await callback_query.message.delete()


@router.callback_query(F.data == 'search_categories')
async def prompt_search(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Prompts for search query input."""
    logger.debug(f"prompt_search called by user {callback_query.from_user.id}")
    await callback_query.message.edit_text(
        escape_markdown(text=_('Please enter your search query:')),
        reply_markup=None
    )
    await state.set_state("category_search")


@router.message(F.state == "category_search")
async def search_categories(message: Message, state: FSMContext) -> None:
    """Handles category search."""
    logger.debug(f"search_categories called by user {message.from_user.id}")
    search_query = message.text.strip()
    if not search_query:
        await message.answer(_("Please enter a valid search query."))
        return

    await state.update_data(search_query=search_query, parent_id=None)
    categories = await get_categories_from_state_or_cache(state)
    user_language = message.from_user.language_code or 'en'

    await show_categories(
        message,
        categories,
        user_language,
        state,
        search_query=search_query
    )
    await state.set_state(None)


@router.callback_query(PaginationCallback.filter())
async def paginate_categories(callback_query: CallbackQuery, callback_data: PaginationCallback,
                              state: FSMContext) -> None:
    """Handles category pagination."""
    page = callback_data.page

    data = await state.get_data()
    categories = data.get('categories')
    search_query = data.get('search_query')
    parent_id = data.get('parent_id')

    if categories is None:
        categories = await get_categories()
        await state.update_data(categories=categories)

    user_language = callback_query.from_user.language_code or 'en'

    await show_categories(
        message_or_query=callback_query,
        categories=categories,
        user_language=user_language,
        state=state,
        parent_id=parent_id,
        search_query=search_query,
        page=page
    )


async def toggle_category_and_children_status(category_id: int):
    async with get_session() as session:
        # Get the category's path
        result = await session.execute(
            select(Category.path, Category.status).where(Category.id == category_id)
        )
        category = result.first()
        if not category:
            return

        new_status = not category.status
        category_path = category.path

        # Update the status of all categories with matching paths
        await session.execute(
            update(Category)
            .where(Category.path.like(f"{category_path}%"))
            .values(status=new_status)
        )

        await session.commit()

    # Update Redis cache
    categories = await get_categories_from_db()
    await set_categories(categories)


async def toggle_child_categories_status(session, parent_id: int, new_status: bool) -> None:
    """Recursively toggles the status of child categories."""
    result = await session.execute(select(Category).where(Category.parent_id == parent_id))
    child_categories = result.scalars().all()
    for child in child_categories:
        child.status = new_status
        await toggle_child_categories_status(session, child.id, new_status)
    logger.debug(f"Child categories of {parent_id} toggled to {new_status}")