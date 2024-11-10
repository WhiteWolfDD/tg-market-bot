from aiogram.filters.state import StatesGroup, State


class PostAdStates(StatesGroup):
    TITLE = State()
    DESCRIPTION = State()
    REASON = State()
    PRICE = State()
    CATEGORY = State()
    MEDIA = State()
    CONFIRM_MEDIA = State()
    LOCATION = State()
    CONTACT_INFO = State()