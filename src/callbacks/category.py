from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State


class CategoryStates(StatesGroup):
    category_search = State()


class CategoryCallback(CallbackData, prefix="category"):
    category_id: int
    action: str  # 'select', 'deselect', 'navigate', 'back'
    parent_id: int | None = None


class PaginationCallback(CallbackData, prefix="paginate"):
    page: int
