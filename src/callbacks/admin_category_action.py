from aiogram.filters.callback_data import CallbackData


class AdminCategoryActionCallback(CallbackData, prefix='admin_category_action'):
    """
    Callback data for admin category action.
    """
    category_id: int
    action: str