from aiogram.filters.callback_data import CallbackData


class SubmitAdCallback(CallbackData, prefix='submit_ad'):
    """
    Submit ad callback.
    """

    pass


class ShowUserAdsCallback(CallbackData, prefix='show_user_ads'):
    """
    Show user ads callback.
    """

    page: int = 0


class AddMediaCallback(CallbackData, prefix='add_media'):
    """
    Add media callback.
    """

    pass


class FinishUploadMediaCallback(CallbackData, prefix='finish_upload'):
    """
    Finish upload media callback.
    """

    pass