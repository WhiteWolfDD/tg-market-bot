import re

from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _

from src.callbacks.main import HomeCallback


def escape_markdown(text: str) -> str:
    """
    Escape markdown characters.
    :param text: The text to escape.
    :return: The escaped text.
    """

    reserved_chars = r'_[]()~>#\+\-=|{}.!'
    return re.sub(f'([{re.escape(reserved_chars)}])', r'\\\1', text)


def build_inline_keyboard(
        keyboard: dict,
        back_cb: str = None,
        home_button: bool = False,
        custom_home_cb: str = None,
        prev_page_cb: str = None,
        next_page_cb: str = None,
        first_page_cb: str = None,
        last_page_cb: str = None
) -> InlineKeyboardBuilder:
    """
    Build an inline keyboard.
    """
    builder = InlineKeyboardBuilder(
        [
            [
                InlineKeyboardButton(
                    text=button['text'],
                    callback_data=button['callback_data'] if 'callback_data' in button else None,
                    url=button['url'] if 'url' in button else None
                ) for button in row if button
            ] for row in keyboard['inline_kbd']
        ]
    )

    if prev_page_cb and next_page_cb:
        buttons = [
            InlineKeyboardButton(
                text='⏮',
                callback_data=first_page_cb
            ) if first_page_cb else None,
            InlineKeyboardButton(
                text=_('⬅️ Prev'),
                callback_data=prev_page_cb
            ),
            InlineKeyboardButton(
                text=_('Next ➡️'),
                callback_data=next_page_cb
            ),
            InlineKeyboardButton(
                text='⏭',
                callback_data=last_page_cb
            ) if last_page_cb else None
        ]

        buttons = [button for button in buttons if button]
        builder.row(*buttons)

    if back_cb:
        builder.row(
            InlineKeyboardButton(
                text=_('⬅️ Back'),
                callback_data=back_cb
            )
        )

    if home_button:
        builder.row(
            InlineKeyboardButton(
                text=_('🏠 Home'),
                callback_data=HomeCallback().pack() if not custom_home_cb else custom_home_cb
            )
        )

    return builder