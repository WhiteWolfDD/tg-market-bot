from aiogram.filters.callback_data import CallbackData


class CategoryCallback(CallbackData, prefix="category"):
    category_id: int
    action: str
    parent_id: int | None = None
    admin_mode: bool = False
