from aiogram.filters.callback_data import CallbackData


class AdminCategoryActionCallback(CallbackData, prefix='admin_category_action'):
    """
    Callback data for admin category action.
    """
    category_id: int
    action: str


class ModerateAdCallback(CallbackData, prefix='moderate_ad'):
    """
    Moderate ad callback.
    """

    ad_id: int = 0
    back: bool = False


class ApproveAdCallback(CallbackData, prefix='approve_ad'):
    """
    Approve ad callback.
    """

    ad_id: int = 0


class RejectAdCallback(CallbackData, prefix='reject_ad'):
    """
    Reject ad callback.
    """

    ad_id: int = 0


class ManageAdAdminCallback(CallbackData, prefix='manage_admin_ad'):
    """
    Manage ad by admin callback.
    """

    ad_id: int = 0


class RenderRequestedAdsCallback(CallbackData, prefix='render_requested_ads'):
    """
    Render requested ads callback.
    """

    pass