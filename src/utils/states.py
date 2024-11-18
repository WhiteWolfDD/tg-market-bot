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


class EditAdStates(StatesGroup):
    MEDIA = State()
    TITLE = State()
    DESCRIPTION = State()
    PRICE = State()
    REASON = State()
    CONTACT_INFO = State()
    LOCATION = State()
    CATEGORY = State()
    HASHTAGS = State()
    MANAGE_AD = State()
