from aiogram.filters.callback_data import CallbackData


class ShowAdvertiseFAQCallback(CallbackData, prefix='show_advertise_faq'):
    """
    Show buy crypto FAQ callback.
    """

    pass


class ShowCostFAQCallback(CallbackData, prefix='show_cost_faq'):
    """
    Show sell crypto FAQ callback.
    """

    pass


class ShowAdsFAQCallback(CallbackData, prefix='show_ads_faq'):
    """
    Show sell crypto FAQ callback.
    """

    pass


class ShowFAQCallback(CallbackData, prefix='show_faq'):
    """
    Show FAQ callback.
    """

    pass
