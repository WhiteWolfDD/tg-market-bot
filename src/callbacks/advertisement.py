from typing import Type

from aiogram.filters.callback_data import CallbackData


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


class ConfirmAdCallback(CallbackData, prefix='confirm_ad'):
    """
    Confirm ad callback.
    """

    pass


class CancelAdCallback(CallbackData, prefix='cancel_ad'):
    """
    Cancel ad callback.
    """

    pass


class ShowApprovedAdsCallback(CallbackData, prefix='show_approved_ads'):
    """
    Show user approved ads callback.
    """

    page: int = 0


class ShowPendingAdsCallback(CallbackData, prefix='show_pending_ads'):
    """
    Show user pending ads callback.
    """

    page: int = 0


class ShowRejectedAdsCallback(CallbackData, prefix='show_rejected_ads'):
    """
    Show user rejected ads callback.
    """

    page: int = 0


class BackToAdsCallback(CallbackData, prefix='back_to_ads'):
    """
    Back to ads callback.
    """

    pass


class ShowAdCallback(CallbackData, prefix='show_ad'):
    """
    Show ad callback.
    """

    ad_id: int = 0


class ManageAdCallback(CallbackData, prefix='manage_ad'):
    """
    Manage ad callback.
    """

    ad_id: int = 0
    admin: bool = False


class EditAdCallback(CallbackData, prefix='edit_ad'):
    """
    Edit ad callback.
    """

    ad_id: int = 0
    admin: bool = False


class EditAdFieldCallback(CallbackData, prefix='edit_ad_field'):
    """
    Edit ad field callback.
    """
    ad_id: int = 0
    field: str = ''


class PaginateAdsCallback(CallbackData, prefix='paginate_ads'):
    """
    Paginate ads callback.
    """

    status: str = ''
    page: int = 0


class DeleteAdCallback(CallbackData, prefix='delete_ad'):
    """
    Delete ad callback.
    """

    ad_id: int = 0


class SendLocationCallback(CallbackData, prefix='send_location'):
    """
    Send location callback.
    """

    pass
