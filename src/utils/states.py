from aiogram.filters.state import StatesGroup, State


class PostAdStates(StatesGroup):
    TITLE = State()
    DESCRIPTION = State()
    PRICE = State()
    CATEGORY = State()
    MEDIA = State()
    LOCATION = State()
    CONTACT_INFO = State()