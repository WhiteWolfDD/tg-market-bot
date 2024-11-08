from aiogram.fsm.state import StatesGroup, State


class OrderCancellationForm(StatesGroup):
    """
    Order cancellation form.
    """

    reason = State()


class ChangeFeeForm(StatesGroup):
    """
    Change fee form.
    """

    commission = State()


class ConfirmPaymentForm(StatesGroup):
    """
    Confirm payment form.
    """

    address = State()
    amount = State()
    payment_id = State()


class ChangeMinAmountForm(StatesGroup):
    """
    Change min amount form.
    """

    min_amount = State()
    crypto_id = State()
