from aiogram.filters.callback_data import CallbackData


class CategoryCallback(CallbackData, prefix="category"):
    """
    Category callback.
    """

    category_id: int
    action: str
    parent_id: int | None = None
    admin_mode: bool = False


class SearchCategoryCallback(CallbackData, prefix="search_category"):
    """
    Search category callback.
    """

    pass


class ConfirmCategorySelectionCallback(CallbackData, prefix="confirm_category_selection"):
    """
    Confirm category selection callback.
    """

    pass
