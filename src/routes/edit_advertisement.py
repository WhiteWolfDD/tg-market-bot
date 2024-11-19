import re

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.utils.i18n import gettext as _

from src.callbacks.admin import ManageAdAdminCallback
from src.callbacks.advertisement import EditAdFieldCallback, EditAdCallback, ManageAdCallback
from src.callbacks.main import DeleteMessageCallback
from src.handlers.advertisement import handle_media_upload, manage_ad
from src.routes.advertisement import format_location
from src.services.advertisement import AdvertisementService
from src.utils.helpers import build_inline_keyboard, escape_markdown, build_edit_ad_keyboard
from src.utils.log import setup_logging
from src.utils.states import EditAdStates

router = Router()
logger = setup_logging()


async def edit_advertisement(callback_query: CallbackQuery, advertisement_id: int, admin: bool = False) -> None:
    msg = _('🛠️ What field would you like to edit? Please choose an option below:')
    kbd = build_inline_keyboard(keyboard=build_edit_ad_keyboard(advertisement_id),
                                back_cb=ManageAdCallback(
                                    ad_id=advertisement_id
                                ).pack() if not admin else ManageAdAdminCallback(ad_id=advertisement_id).pack())

    await callback_query.message.edit_text(text=escape_markdown(msg), reply_markup=kbd.as_markup())


@router.callback_query(EditAdFieldCallback().filter())
async def edit_ad_field(callback_query: CallbackQuery, callback_data: EditAdFieldCallback, state: FSMContext) -> None:
    ad_id, field = callback_data.ad_id, callback_data.field

    field_messages = {
        'media': (_('📷 Please send me a new photo or video for this advertisement.'), 'media'),
        'title': (_('📝 Please send me a new title for this advertisement.'), 'title'),
        'description': (_('📄 Please send me a new description for this advertisement.'), 'description'),
        'price': (_('💰 Please send me a new price for this advertisement.'), 'price'),
        'reason': (_('📝 Please send me a new reason for selling this item.'), 'reason'),
        'contact_info': (
            _('📞 Please send me new contact information for this advertisement.'), 'contact_info'),
        'location': (_('📍 Please send me a new location for this advertisement.'), 'location'),
        'category': (_('📦 Please send me a new category for this advertisement.'), 'category'),
        'hashtags': (_('🔖 Please send me new hashtags for this advertisement.'), 'hashtags')
    }

    if field in field_messages:
        msg, state_name = field_messages[field]
        await edit_advertisement_field(callback_query, ad_id, state, msg, state_name)
    else:
        await unknown_field(callback_query)
        logger.error(f'Unknown field: {field}')


async def unknown_field(callback_query: CallbackQuery) -> None:
    await callback_query.answer(_('Unknown field.'), show_alert=True)


async def edit_advertisement_field(
        callback_query: CallbackQuery,
        ad_id: int,
        state: FSMContext,
        msg: str,
        state_name: str
) -> None:
    if state_name == 'location':
        kbd = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=_('📍 Share Location'), request_location=True)]],
            resize_keyboard=True
        )
        await callback_query.message.answer(text=escape_markdown(msg), reply_markup=kbd)
    else:
        kbd = build_inline_keyboard(
            {'inline_kbd': [[{'text': _('❌ Cancel'), 'callback_data': DeleteMessageCallback(
                message_id=callback_query.message.message_id).pack()}]]},
            back_cb=EditAdCallback(ad_id=ad_id).pack()
        )
        await callback_query.message.edit_text(text=escape_markdown(msg), reply_markup=kbd.as_markup())

    await state.set_state(getattr(EditAdStates, state_name.upper()))
    await state.update_data(ad_id=ad_id)


@router.message(EditAdStates.MEDIA)
async def edit_ad_media_handler(message: Message, state: FSMContext) -> None:
    await handle_media_upload(message, state)


async def edit_ad_field_handler(message: Message, state: FSMContext, field: str) -> None:
    try:
        data = await state.get_data()
        ad_id = data.get('ad_id')

        if field == 'hashtags':
            hashtags = re.split(r'[,\s]+', message.text.strip())
            hashtags = [tag if tag.startswith('#') else f'#{tag}' for tag in hashtags if tag]
            hashtags = list(dict.fromkeys(hashtags))
            await AdvertisementService.update_advertisement(ad_id, **{field: hashtags})
        else:
            await AdvertisementService.update_advertisement(ad_id, **{field: message.text})

        await message.answer(escape_markdown(f'✅ {field} ' + _('has been successfully updated.')))
        await manage_ad(message, ad_id)
    except Exception as e:
        logger.error(f'Failed to update advertisement field: {e}')
        await message.answer(escape_markdown(_('🙇‍♂️ Failed to update the advertisement field.')))


field_handlers = {
    EditAdStates.TITLE: 'title',
    EditAdStates.DESCRIPTION: 'description',
    EditAdStates.PRICE: 'price',
    EditAdStates.REASON: 'reason',
    EditAdStates.CONTACT_INFO: 'contact_info',
    EditAdStates.CATEGORY: 'category',
    EditAdStates.HASHTAGS: 'hashtags'
}

for state, field in field_handlers.items():
    @router.message(state)
    async def handler(message: Message, state: FSMContext, field=field) -> None:
        await edit_ad_field_handler(message, state, field)


@router.message(EditAdStates.LOCATION)
async def edit_ad_location_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    ad_id = data.get('ad_id')

    try:
        location = message.location
        if not location:
            await message.answer(_("Please share your location."))
            return
        location_text = await format_location(location)

        await AdvertisementService.update_advertisement(ad_id, location=location_text)
        await message.answer(escape_markdown(_('📍 Location has been successfully updated.')))
        await manage_ad(message, ad_id)
    except Exception as e:
        logger.error(f'Failed to update location for ad_id {ad_id}: {e}')
        await message.answer(escape_markdown(_('🙇‍♂️ Failed to update the location.')))
