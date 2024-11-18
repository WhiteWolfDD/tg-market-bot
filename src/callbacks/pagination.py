from aiogram.filters.callback_data import CallbackData


class ExceptionPaginationCallback(CallbackData, prefix='pagination'):
    """
    Callback data for pagination.
    """
    page: int


class CategoryPaginationCallback(CallbackData, prefix='category_pagination'):
    """
    Callback data for category pagination.
    """
    page: int


class ModeratePaginationCallback(CallbackData, prefix='moderate_pagination'):
    """
    Callback data for user advertisements moderation pagination.
    """
    page: int
