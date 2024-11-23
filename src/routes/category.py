import asyncio
import os
import math
from typing import List, Dict, Any

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from src.callbacks.category import CategoryCallback, SearchCategoryCallback, ConfirmCategorySelectionCallback
from src.callbacks.main import CancelActionCallback
from src.callbacks.pagination import CategoryPaginationCallback
from src.callbacks.admin import AdminCategoryActionCallback
from src.utils.helpers import escape_markdown, build_inline_keyboard
from src.services.category import CategoryService
from src.utils.log import setup_logging
from src.utils.states import PostAdStates

logger = setup_logging()
router = Router()


def is_admin(user_id: int) -> bool:
    """
    Check if the user is an admin.

    :param user_id: The ID of the user.
    :return: True if the user is an admin, False otherwise.
    """
    admins = os.getenv('ADMIN_ID').split(',')
    for admin in admins:
        if str(user_id) == admin:
            return True
    return False


def get_category_name(category: Dict[str, Any], language_code: str) -> str:
    """
    Get the name of the category in the specified language.

    :param category: The category dictionary.
    :param language_code: The language code.
    :return: The name of the category in the specified language.
    """
    translations = category['translations']
    return next(
        (t['name'] for t in translations if t['language_code'] == language_code),
        next((t['name'] for t in translations if t['language_code'] == 'en'), None)
    )


async def get_categories_from_state_or_cache(state: FSMContext) -> List[Dict[str, Any]]:
    """
    Retrieve categories from the FSM state or cache.

    :param state: The FSM context.
    :return: The list of categories.
    """
    data = await state.get_data()
    categories = data.get('categories')
    if categories is None:
        categories = await CategoryService.get_categories()
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
    """
    Display categories to the user.

    :param message_or_query: The message or callback query.
    :param categories: The list of categories.
    :param user_language: The user's language code.
    :param state: The FSM context.
    :param parent_id: The parent category ID, defaults to None.
    :param search_query: The search query, defaults to None.
    :param admin_mode: Whether admin mode is enabled, defaults to False.
    :param page: The current page number, defaults to 1.
    :param page_size: The number of categories per page, defaults to 30.
    """
    logger.debug(f"show_categories called with parent_id={parent_id}, search_query={search_query}, page={page}, admin_mode={admin_mode}")

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

    # Check if the user is an admin
    user_id = message_or_query.from_user.id if isinstance(message_or_query, CallbackQuery) else message_or_query.chat.id
    is_user_admin = is_admin(user_id)

    if is_user_admin and admin_mode:
        # Admin: show all categories
        display_categories = filtered_categories[(page - 1) * page_size: page * page_size]
        logger.debug(f"Admin mode: Displaying all categories. Total: {len(display_categories)}")
    else:
        # User: show only active categories
        paginated_categories = filtered_categories[(page - 1) * page_size: page * page_size]
        display_categories = [
            category for category in paginated_categories
            if category.get('status', True)
        ]
        logger.debug(f"User mode: Displaying active categories. Total: {len(display_categories)}")

    total_pages = math.ceil(len(filtered_categories) / page_size)

    kbd = build_inline_keyboard(
        keyboard={
            'inline_kbd': [
                [
                    {
                        'text': f"{('🟢' if category.get('status', True) else '🔴') if admin_mode else ''} "
                                f"{category['emoji']} {get_category_name(category, user_language)}",
                        'callback_data': CategoryCallback(
                            category_id=category['id'],
                            action='navigate',
                            parent_id=category['parent_id'],
                            admin_mode=admin_mode
                        ).pack()
                    }
                ] for category in display_categories
            ] + [
                [
                    {
                        'text': _('🔍 Search categories'),
                        'callback_data': SearchCategoryCallback().pack()
                    }
                ]
            ]
        },
        back_cb=CancelActionCallback().pack() if parent_id is not None else None,
        prev_page_cb=CategoryPaginationCallback(page=page - 1).pack() if page > 1 else None,
        next_page_cb=CategoryPaginationCallback(page=page + 1).pack() if page < total_pages else None,
        request_location=False
    )

    category_text = escape_markdown(_("Please select a category:"))
    if search_query:
        category_text += f" '{search_query}'"

    if isinstance(message_or_query, Message):
        await message_or_query.answer(escape_markdown(text=category_text), reply_markup=kbd.as_markup())
    elif isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(escape_markdown(text=category_text), reply_markup=kbd.as_markup())
        await message_or_query.answer()


@router.callback_query(CategoryCallback.filter())
async def navigate_category(callback_query: CallbackQuery, callback_data: CategoryCallback, state: FSMContext,
                            admin_mode: bool = False) -> None:
    """
    Handle category navigation.

    :param callback_query: The callback query.
    :param callback_data: The callback data.
    :param state: The FSM context.
    :param admin_mode: Whether admin mode is enabled, defaults to False.
    """
    logger.debug(f"navigate_category called by user {callback_query.from_user.id} with data {callback_data}")

    admin_mode = admin_mode or callback_data.admin_mode

    categories = await get_categories_from_state_or_cache(state)
    selected_category = next((cat for cat in categories if cat['id'] == callback_data.category_id), None)
    if not selected_category:
        await callback_query.answer(_("Category not found."), show_alert=True)
        return

    if is_admin(callback_query.from_user.id) and admin_mode:
        await handle_admin_category_selection(callback_query, selected_category, categories)
    else:
        await handle_user_category_selection(callback_query, selected_category, categories, state)


async def handle_admin_category_selection(callback_query: CallbackQuery, category: Dict[str, Any],
                                          categories: List[Dict[str, Any]]) -> None:
    """
    Handle category selection by an admin.

    :param callback_query: The callback query.
    :param category: The selected category.
    :param categories: The list of categories.
    """
    child_categories = [cat for cat in categories if cat['parent_id'] == category['id']]
    buttons = [
        [InlineKeyboardButton(text=escape_markdown(_('➡️ Go to child categories')),
                              callback_data=AdminCategoryActionCallback(category_id=category['id'],
                                                                        action='go_to_children').pack())] if child_categories else [],
        [InlineKeyboardButton(text=escape_markdown(_('✅ Confirm category (Don\'t use in Category Edit)'),),
                              callback_data=ConfirmCategorySelectionCallback().pack())] if not child_categories else [],
        [InlineKeyboardButton(text=escape_markdown(_('🔄 Toggle category status')),
                              callback_data=AdminCategoryActionCallback(category_id=category['id'],
                                                                        action='toggle_status').pack())],
        [InlineKeyboardButton(text=escape_markdown(_('❌ Cancel')), callback_data=CancelActionCallback().pack())]
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    category_name = get_category_name(category, callback_query.from_user.language_code or 'en')

    await callback_query.message.edit_text(escape_markdown(
        text=_('You have selected the category: {category_name}\nChoose an action:').format(
            category_name=category_name)), reply_markup=keyboard)
    await callback_query.answer()


async def handle_user_category_selection(callback_query: CallbackQuery, category: Dict[str, Any],
                                         categories: List[Dict[str, Any]], state: FSMContext) -> None:
    """
    Handle category selection by a user.

    :param callback_query: The callback query.
    :param category: The selected category.
    :param categories: The list of categories.
    :param state: The FSM context.
    """
    child_categories = [cat for cat in categories if cat['parent_id'] == category['id'] and cat.get('status', True)]
    await state.update_data(selected_category=category)

    if child_categories:
        await show_categories(callback_query, categories, callback_query.from_user.language_code or 'en', state,
                              parent_id=category['id'])
    else:
        kbd = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('✅ Confirm'), callback_data=ConfirmCategorySelectionCallback().pack())],
            [InlineKeyboardButton(text=_('❌ Cancel'), callback_data=CancelActionCallback().pack())]
        ])
        category_name = get_category_name(category, callback_query.from_user.language_code or 'en')
        await callback_query.message.edit_text(escape_markdown(
            text=_('You have selected the category: {category_name}\n\n✅ Confirm your selection:').format(
                category_name=category_name)), reply_markup=kbd)
        await callback_query.answer()


@router.callback_query(AdminCategoryActionCallback.filter())
async def handle_admin_category_action(callback_query: CallbackQuery, callback_data: AdminCategoryActionCallback,
                                       state: FSMContext) -> None:
    """
    Handle admin category actions.

    :param callback_query: The callback query.
    :param callback_data: The callback data.
    :param state: The FSM context.
    """
    await callback_query.answer()

    if callback_data.action == 'toggle_status':
        await callback_query.message.edit_text(
            escape_markdown(_("⏳ Processing, please wait...\n\n It may take a while.")))
        asyncio.create_task(process_admin_action(callback_query, callback_data, state))
    elif callback_data.action == 'go_to_children':
        categories = await get_categories_from_state_or_cache(state)
        await show_categories(callback_query, categories, callback_query.from_user.language_code or 'en', state,
                              parent_id=callback_data.category_id, admin_mode=True)
    else:
        await callback_query.answer(_("Unknown action."), show_alert=True)


async def process_admin_action(
    callback_query: CallbackQuery,
    callback_data: AdminCategoryActionCallback,
    state: FSMContext
):
    """
    Process admin actions asynchronously.

    :param callback_query: The callback query.
    :param callback_data: The callback data.
    :param state: The FSM context.
    """
    try:
        await CategoryService.toggle_category_and_children_status(callback_data.category_id)

        categories = await CategoryService.get_categories_from_cache()
        await state.update_data(categories=categories)

        await callback_query.message.edit_text(escape_markdown(_("✅ Category status updated.")))
        state_data = await state.get_data()
        parent_id = state_data.get('parent_id')

        await show_categories(
            message_or_query=callback_query.message,
            categories=categories,
            user_language=callback_query.from_user.language_code or 'en',
            state=state,
            parent_id=parent_id,
            admin_mode=True
        )
    except Exception as e:
        logger.error(f"Error updating category status: {e}")
        await callback_query.message.answer(
            escape_markdown(_("An error occurred while updating the category status."))
        )


@router.callback_query(CancelActionCallback().filter())
async def cancel_last_action(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Cancel the last action.

    :param callback_query: The callback query.
    :param state: The FSM context.
    """
    logger.debug(f"cancel_last_action called by user {callback_query.from_user.id}")
    await state.clear()
    await callback_query.answer(_("Action canceled."))

    categories = await CategoryService.get_categories()
    await show_categories(callback_query, categories, callback_query.from_user.language_code or 'en', state,
                          admin_mode=True)


@router.callback_query(ConfirmCategorySelectionCallback().filter())
async def confirm_category_selection(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Confirm the selected category.

    :param callback_query: The callback query.
    :param state: The FSM context.
    """
    logger.debug(f"confirm_category_selection called by user {callback_query.from_user.id}")
    data = await state.get_data()
    selected_category = data.get('selected_category')
    logger.debug(f"Selected category: {selected_category}")

    if not selected_category:
        await callback_query.answer(_("Please select a category first."))
        return

    await state.update_data(selected_category=selected_category)
    await callback_query.message.answer(escape_markdown(
        text=_(
            '📤 *Post an ad*\n\n📸 Send me the *media* of the ad.\n\n❗️ Limit per one file - *45 MB*\n\n🚫 Send /cancel to cancel the operation.'))
    )
    await state.set_state(PostAdStates.MEDIA)


@router.callback_query(SearchCategoryCallback().filter())
async def prompt_search(callback_query: CallbackQuery, state: FSMContext) -> None:
    """
    Prompt the user to enter a search query.

    :param callback_query: The callback query.
    :param state: The FSM context.
    """

    logger.debug(f"prompt_search called by user {callback_query.from_user.id}")
    await callback_query.message.edit_text(escape_markdown(text=_('Please enter your search query:')),
                                           reply_markup=None)
    await state.set_state(PostAdStates.CATEGORY_SEARCH)


@router.message(PostAdStates.CATEGORY_SEARCH)
async def search_categories(message: Message, state: FSMContext) -> None:
    """
    Search for categories based on the user's query.

    :param message: The message containing the search query.
    :param state: The FSM context.
    """
    logger.debug(f"search_categories called by user {message.from_user.id}")
    search_query = message.text.strip()
    if not search_query:
        await message.answer(_("Please enter a valid search query."))
        return

    await state.update_data(search_query=search_query, parent_id=None)
    categories = await get_categories_from_state_or_cache(state)
    await show_categories(message, categories, message.from_user.language_code or 'en', state,
                          search_query=search_query)
    await state.set_state(None)


@router.callback_query(CategoryPaginationCallback.filter())
async def paginate_categories(callback_query: CallbackQuery, callback_data: CategoryPaginationCallback,
                              state: FSMContext) -> None:
    """
    Handle pagination of categories.

    :param callback_query: The callback query.
    :param callback_data: The callback data.
    :param state: The FSM context.
    """
    page = callback_data.page
    data = await state.get_data()
    categories = data.get('categories') or await CategoryService.get_categories()
    await state.update_data(categories=categories)

    await show_categories(
        message_or_query=callback_query,
        categories=categories,
        user_language=callback_query.from_user.language_code or 'en',
        state=state,
        parent_id=data.get('parent_id'),
        search_query=data.get('search_query'),
        page=page,
        admin_mode=is_admin(callback_query.from_user.id)
    )