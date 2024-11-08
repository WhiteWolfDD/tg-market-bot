from aiogram.filters.callback_data import CallbackData


class PaginationCallback(CallbackData, prefix='pagination'):
    """
    Callback data for pagination.
    """
    page: int
