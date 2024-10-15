from aiogram.filters.callback_data import CallbackData


class HomeCallback(CallbackData, prefix='home'):
    """
    Go to the home page.
    """

    pass


class EmptyCallback(CallbackData, prefix='empty'):
    """
    Empty callback.
    """

    pass


class DeleteMessageCallback(CallbackData, prefix='delete_message'):
    """
    Delete message callback.
    """

    message_id: int
