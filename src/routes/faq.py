from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from src.callbacks.faq import ShowAdvertiseFAQCallback, ShowCostFAQCallback, ShowAdsFAQCallback, ShowFAQCallback
from src.utils.helpers import escape_markdown, build_inline_keyboard

router = Router()


@router.message(F.text == '📚 FAQ')
async def show_faq(message: Message) -> None:
    """
    Handle showing FAQ.
    """

    msg, kbd = await render_faq()
    await message.answer(
        text=escape_markdown(text=msg),
        reply_markup=build_inline_keyboard(
            keyboard=kbd
        ).as_markup()
    )


@router.callback_query(ShowAdvertiseFAQCallback.filter())
async def show_advertise_faq(query: CallbackQuery) -> None:
    """
    Handle showing advertise FAQ.
    """

    msg = (
        _('❕ *How to advertise on the platform?*\n\n'
          '1️⃣ Click on the *"📤 Post an ad"* button in the main menu to start posting an ad.\n\n'
          '2️⃣ Fill in the required fields: *title*, *description*, *price*, *category*, *location*.\n\n'
          '3️⃣ Upload *photos* of the product you are selling.\n\n'
          '4️⃣ Click on the *"📤 Post"* button to publish the ad.\n\n'
          '5️⃣ Wait for the ad to be *approved* by the moderator.\n\n'
          '6️⃣ Once the ad is approved, it will be available for viewing by other users.')
    )

    kbd = {'inline_kbd': []}

    await query.answer()
    await query.message.edit_text(
        text=escape_markdown(text=msg),
        reply_markup=build_inline_keyboard(
            keyboard=kbd,
            back_cb=ShowFAQCallback().pack()
        ).as_markup()
    )


@router.callback_query(ShowCostFAQCallback.filter())
async def show_cost_faq(query: CallbackQuery) -> None:
    """
    Handle showing cost FAQ.
    """

    msg = (
        _('❕ *What is the cost of advertising?*\n\n'
          '🔹 The cost of advertising on the platform is *free*.\n\n'
          '🔹 You can post an unlimited number of ads without any restrictions.')
    )

    kbd = {
        'inline_kbd': []
    }

    await query.answer()
    await query.message.edit_text(
        text=escape_markdown(text=msg),
        reply_markup=build_inline_keyboard(
            keyboard=kbd,
            back_cb=ShowFAQCallback().pack()
        ).as_markup()
    )


@router.callback_query(ShowAdsFAQCallback.filter())
async def show_ads_faq(query: CallbackQuery) -> None:
    """
    Handle showing ads FAQ.
    """

    msg = (
        _('❕ *What we do with your ads?*\n\n'
          '🔹 We *moderate* all ads before they are published on the platform.\n\n'
          '🔹 We *check* the ad for compliance with the rules of the platform.\n\n'
          '🔹 We *approve* the ad if it meets the requirements.')
    )

    kbd = {
        'inline_kbd': []
    }

    await query.answer()
    await query.message.edit_text(
        text=escape_markdown(text=msg),
        reply_markup=build_inline_keyboard(
            keyboard=kbd,
            back_cb=ShowFAQCallback().pack()
        ).as_markup()
    )


@router.callback_query(ShowFAQCallback.filter())
async def back_to_faq(query: CallbackQuery) -> None:
    """
    Handle back to FAQ.
    """
    msg, kbd = await render_faq()
    await query.answer()
    await query.message.edit_text(
        text=escape_markdown(text=msg),
        reply_markup=build_inline_keyboard(
            keyboard=kbd
        ).as_markup()
    )


async def render_faq() -> tuple[str, dict]:
    """
    Render FAQ.
    """

    msg = (
        _('📚 *FAQ*\n\n'
          '👇 Here you can find answers to frequently asked questions.\n\n'
          '🔹 *How to advertise on the platform?*\n'
          '🔹 *What is the cost of advertising?*\n'
          '🔹 *What we do with your ads?*\n'
          '👇 *Choose a question* to get an answer.')
    )

    kbd = {
        'inline_kbd': [
            [
                {'text': _('🔹 How to advertise on the platform?'), 'callback_data': ShowAdvertiseFAQCallback().pack()}
            ],
            [
                {'text': _('🔹 What is the cost of advertising?'), 'callback_data': ShowCostFAQCallback().pack()}
            ],
            [
                {'text': _('🔹 What we do with your ads?'), 'callback_data': ShowAdsFAQCallback().pack()}
            ]
        ]
    }

    return msg, kbd
