from aiogram.filters.callback_data import CallbackData


class AdminHomePageCallback(CallbackData, prefix='admin_homepage'):
    """
    Admin homepage callback.
    """

    pass


class ShowAdminPaymentsCallback(CallbackData, prefix='admin_payments'):
    """
    Show admin payments callback.
    """

    page: int = 0


class ShowAdminWithdrawalsCallback(CallbackData, prefix='admin_withdrawals'):
    """
    Show admin withdrawals callback.
    """

    page: int = 0


class ShowWithdrawalDetailsCallback(CallbackData, prefix='admin_show_withdrawal_details'):
    """
    Show withdrawal details callback.
    """

    wallet_order_id: int


class ShowAdminDepositCallback(CallbackData, prefix='admin_deposit'):
    """
    Show admin deposit callback.
    """

    page: int = 0


class ShowDepositDetailsCallback(CallbackData, prefix='admin_show_deposit_details'):
    """
    Show deposit details callback.
    """

    wallet_order_id: int


class ShowPaymentDetailsCallback(CallbackData, prefix='admin_show_payment_details'):
    """
    Show payment details callback.
    """

    payment_id: int


class ConfirmPaymentCallback(CallbackData, prefix='complete_payment'):
    """
    Confirm payment callback.
    """

    pass

class ConfirmSellPaymentCallback(CallbackData, prefix='complete_sell_payment'):
    """
    Confirm sell payment callback.
    """

    payment_id: int


class CancelSellPaymentCallback(CallbackData, prefix='cancel_sell_payment'):
    """
    Cancel sell payment callback.
    """

    payment_id: int


class AcceptWithdrawCallback(CallbackData, prefix='accept_withdraw'):
    """
    Accept withdraw callback.
    """

    user_id: int
    wallet_order_id: int
    amount: float


class RejectWithdrawCallback(CallbackData, prefix='reject_withdraw'):
    """
    Reject withdraw callback.
    """

    user_id: int
    wallet_order_id: int
    amount: float


class AcceptDepositCallback(CallbackData, prefix='accept_deposit'):
    """
    Accept deposit callback.
    """

    user_id: int
    wallet_order_id: int
    amount: float


class RejectDepositCallback(CallbackData, prefix='reject_deposit'):
    """
    Reject deposit callback.
    """

    user_id: int
    wallet_order_id: int
    amount: float


class ConfirmPaymentCancellationCallback(CallbackData, prefix='c'):
    """
    Confirm payment cancellation callback.
    """

    payment_id: int


class CancelPaymentCallback(CallbackData, prefix='cancel_payment'):
    """
    Cancel payment callback.
    """

    payment_id: int


class ViewExceptionLogCallback(CallbackData, prefix='view_exception_log'):
    """
    View exception log callback.
    """

    filename: str


class DeleteExceptionLogsCallback(CallbackData, prefix='delete_exception_logs'):
    """
    Delete exception logs callback.
    """

    pass


class EditCommissionCallback(CallbackData, prefix='edit_commission'):
    """
    Edit commission callback.
    """

    crypto_id: int
    commission: float


class ShowAdminCryptoCallback(CallbackData, prefix='admin_show_crypto'):
    """
    Show admin crypto callback.
    """

    pass


class ShowSwitchCryptoCallback(CallbackData, prefix='switch_crypto_show'):
    """
    Switch crypto callback.
    """

    pass


class SwitchCryptoCallback(CallbackData, prefix='switch_crypto'):
    """
    Switch crypto callback.
    """

    crypto_id: int
    buy_enabled: bool
    sell_enabled: bool


class ShowChangeMinAmountCallback(CallbackData, prefix='show_change_min_amount'):
    """
    Show change min amount callback.
    """

    pass


class ShowCryptoChangeMinAmountCallback(CallbackData, prefix='show_crypto_change_min_amount'):
    """
    Show crypto change min amount callback.
    """

    crypto_id: int