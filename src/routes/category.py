from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import gettext as _
from aiogram import Router, F
from typing import List, Dict, Any
import math

from src.callbacks.category import CategoryCallback, CategoryStates, PaginationCallback
from src.utils.helpers import build_inline_keyboard, escape_markdown
from src.utils.cache import get_categories
from src.utils.log import setup_logging

logger = setup_logging()
router = Router()



async def show_categories(
        message_or_query: Message | CallbackQuery,
        categories: List[Dict[str, Any]],
        user_language: str,
        state: FSMContext,
        parent_id: int = None,
        search_query: str = None,
        page: int = 1,
        page_size: int = 30
) -> None:
    """Отображение категорий с навигацией и поиском."""
    logger.debug(f"show_categories called with parent_id={parent_id}, search_query={search_query}, page={page}")

    if categories is None:
        await message_or_query.answer(_("No categories found."))
        return

    # Обновляем parent_id в данных состояния
    await state.update_data(parent_id=parent_id)

    data = await state.get_data()
    selected_categories = data.get('selected_categories', [])

    buttons = []

    # Фильтрация категорий на основе parent_id и search_query
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

    # Рассчитываем пагинацию
    total_pages = math.ceil(len(filtered_categories) / page_size)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paginated_categories = filtered_categories[start_index:end_index]

    for category in paginated_categories:
        translations = category['translations']
        category_name = next(
            (t['name'] for t in translations if t['language_code'] == user_language),
            next((t['name'] for t in translations if t['language_code'] == 'en'), None)
        )

        buttons.append({
            'text': f"{'✅ ' if category['id'] in selected_categories else ''}{category['emoji']} {category_name}",
            'callback_data': CategoryCallback(
                category_id=category['id'],
                action='navigate',
                parent_id=category['parent_id']
            ).pack()
        })

    # Добавить кнопку поиска
    buttons.append({
        'text': _('🔍 Search'),
        'callback_data': 'search_categories'
    })

    # Добавить кнопки пагинации
    pagination_buttons = []
    if page > 1:
        pagination_buttons.append({
            'text': _('⬅️ Back'),
            'callback_data': PaginationCallback(page=page - 1).pack()
        })
    if page < total_pages:
        pagination_buttons.append({
            'text': _('➡️ Forward'),
            'callback_data': PaginationCallback(page=page + 1).pack()
        })
    if pagination_buttons:
        buttons.extend(pagination_buttons)

    if len(buttons) == 0:
        await message_or_query.answer(_("No categories found."))
        return

    inline_keyboard_structure = {'inline_kbd': [buttons[i:i + 2] for i in range(0, len(buttons), 2)]}

    # Добавить кнопку "Назад", если есть родительская категория
    back_cb = None
    if parent_id is not None:
        back_cb = CategoryCallback(category_id=parent_id, action='back', parent_id=None).pack()

    keyboard = build_inline_keyboard(
        keyboard=inline_keyboard_structure,
        back_cb=back_cb
    ).as_markup()

    text = _('Please select a category:')
    if search_query:
        text += f" '{search_query}'"

    if isinstance(message_or_query, Message):
        await message_or_query.answer(
            escape_markdown(text=text),
            reply_markup=keyboard
        )
    elif isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_text(
            escape_markdown(text=text),
            reply_markup=keyboard
        )
        await message_or_query.answer()


@router.callback_query(CategoryCallback.filter())
async def navigate_category(callback_query: CallbackQuery, callback_data: CategoryCallback, state: FSMContext) -> None:
    """Обработка навигации и выбора категории."""
    logger.debug(f"navigate_category called by user {callback_query.from_user.id} with data {callback_data}")

    # Получаем категории из состояния или кэша
    data = await state.get_data()
    categories = data.get('categories')
    if categories is None:
        categories = await get_categories()
        await state.update_data(categories=categories)

    selected_categories = data.get('selected_categories', [])
    user_language = callback_query.from_user.language_code or 'en'

    selected_category = next((cat for cat in categories if cat['id'] == callback_data.category_id), None)
    if not selected_category:
        await callback_query.answer(_("Category not found."), show_alert=True)
        return

    if callback_data.action == 'navigate':
        # Сбрасываем search_query при навигации по категориям
        await state.update_data(search_query=None)

        child_categories = [cat for cat in categories if cat['parent_id'] == selected_category['id']]
        if child_categories:
            await show_categories(callback_query, categories, user_language, state, parent_id=selected_category['id'])
        else:
            if selected_category['id'] in selected_categories:
                selected_categories.remove(selected_category['id'])
            else:
                selected_categories.append(selected_category['id'])
            await state.update_data(selected_categories=selected_categories)
            await callback_query.answer(_("Category selected."))
    elif callback_data.action == 'back':
        parent_id = selected_category['parent_id']
        await show_categories(callback_query, categories, user_language, state, parent_id=parent_id)


@router.callback_query(F.data == 'search_categories')
async def prompt_search(callback_query: CallbackQuery, state: FSMContext) -> None:
    """Запрос ввода поискового запроса у пользователя."""
    await callback_query.message.edit_text(
        escape_markdown(text=_('Please enter your search query:')),
        reply_markup=None
    )
    await callback_query.answer()
    await state.set_state(CategoryStates.category_search)
    logger.debug(f"State set to 'category_search' for user {callback_query.from_user.id}")


@router.message(CategoryStates.category_search)
async def search_categories(message: Message, state: FSMContext) -> None:
    """Обработка поиска категорий."""
    logger.debug(f"search_categories called by user {message.from_user.id}")
    search_query = message.text.strip()
    if not search_query:
        await message.answer(_("Please enter a valid search query."))
        return

    # Сохраняем поисковый запрос и сбрасываем parent_id
    await state.update_data(search_query=search_query, parent_id=None)

    # Получаем категории из состояния или кэша
    data = await state.get_data()
    categories = data.get('categories')
    if not categories:
        categories = await get_categories()
        await state.update_data(categories=categories)

    user_language = message.from_user.language_code or 'en'

    await show_categories(message, categories, user_language, state, search_query=search_query)
    await state.set_state(None)  # Сбрасываем состояние FSM, но сохраняем данные


@router.callback_query(PaginationCallback.filter())
async def paginate_categories(callback_query: CallbackQuery, callback_data: PaginationCallback, state: FSMContext) -> None:
    """Обработка пагинации категорий."""
    page = callback_data.page

    data = await state.get_data()
    categories = data.get('categories')
    search_query = data.get('search_query')  # Получаем поисковый запрос из состояния
    parent_id = data.get('parent_id')  # Получаем parent_id из состояния

    # Если категории не сохранены в состоянии, получаем их
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