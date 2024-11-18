from aiogram.filters.callback_data import CallbackData


class ViewExceptionLogCallback(CallbackData, prefix="view_exception_log"):
    """
    View exception log callback.
    """

    log: str


class DeleteExceptionLogsCallback(CallbackData, prefix="delete_exception_logs"):
    """
    Delete exception logs callback.
    """

    pass


class DeleteExceptionLogCallback(CallbackData, prefix="delete_exception_log"):
    """
    Delete exception log callback.
    """

    log: str