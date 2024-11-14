import os

from aiogram import Router
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from src.callbacks.category import PaginationCallback
from src.callbacks.exception_logs import ViewExceptionLogCallback, \
    DeleteExceptionLogsCallback, DeleteExceptionLogCallback
from src.callbacks.main import DeleteMessageCallback
from src.utils.const import LogsConfig
from src.utils.helpers import escape_markdown, build_inline_keyboard
from src.utils.log import setup_logging

logger = setup_logging()
router = Router()


async def render_exception_logs(target: Message | CallbackQuery, page: int = 1) -> None:
    """
    Render exception logs with pagination.

    :param target: Message or CallbackQuery
    :param page: Current page number
    :return:
    """
    storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'logs', 'exceptions')
    logs = [log for log in os.listdir(storage_path) if log.endswith('.log')]
    logs.sort(reverse=True)

    if not logs:
        if isinstance(target, Message):
            await target.answer(
                text=escape_markdown(
                    text=_('📜 *Error logs*.\n\nNo logs found.')
                )
            )
        else:
            await target.message.edit_text(
                text=escape_markdown(
                    text=_('📜 *Error logs*.\n\nNo logs found.')
                )
            )
        return

    total_pages = (len(logs) + LogsConfig.LOGS_PER_PAGE) - 1 // LogsConfig.LOGS_PER_PAGE

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start = (page - 1) * LogsConfig.LOGS_PER_PAGE
    end = start + LogsConfig.LOGS_PER_PAGE
    current_logs = logs[start:end]

    msg = _('📜 *Error logs*.\n\nSelect a log to view.')

    buttons = [
        [
            InlineKeyboardButton(text=f'📄 {log}', callback_data=ViewExceptionLogCallback(log=log).pack())
            for log in current_logs[i:i + LogsConfig.LOGS_PER_ROW]
        ] for i in range(0, len(current_logs), LogsConfig.LOGS_PER_ROW)
    ]

    pagination_buttons = []
    if page > 1:
        pagination_buttons.append(InlineKeyboardButton(
            text=_('⬅️ Previous'),
            callback_data=PaginationCallback(page=page - 1).pack()
        ))
    if page < total_pages:
        pagination_buttons.append(InlineKeyboardButton(
            text=_('➡️ Next'),
            callback_data=PaginationCallback(page=page + 1).pack()
        ))

    buttons.append(
        [InlineKeyboardButton(text=_('🗑 Delete all logs'), callback_data=DeleteExceptionLogsCallback().pack())]
    )
    if pagination_buttons:
        buttons.append(pagination_buttons)

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    if isinstance(target, Message):
        await target.answer(
            text=escape_markdown(text=msg),
            reply_markup=keyboard
        )
    elif isinstance(target, CallbackQuery):
        await target.message.edit_text(
            text=escape_markdown(text=msg),
            reply_markup=keyboard
        )


@router.callback_query(ViewExceptionLogCallback.filter())
async def view_exception_log(query: CallbackQuery, callback_data: ViewExceptionLogCallback) -> None:
    """
    View exception log.

    :param query:
    :param callback_data:
    :return:
    """

    log_file = callback_data.log

    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'logs',
                             'exceptions', log_file)

    msg = _('📜 *Error log*.\n\n'
            'Log file is attached below.')

    client_message = await query.bot.send_document(
        document=FSInputFile(file_path),
        caption=escape_markdown(text=msg),
        chat_id=query.message.chat.id
    )

    # Prepare keyboard
    kbd = {
        'inline_kbd': [
            [
                {'text': '🫣 Hide', 'callback_data': DeleteMessageCallback(message_id=client_message.message_id).pack()},
                {'text': '🗑 Delete', 'callback_data': DeleteExceptionLogCallback(log=log_file).pack()},
            ]
        ]
    }

    await query.bot.edit_message_reply_markup(
        chat_id=client_message.chat.id,
        message_id=client_message.message_id,
        reply_markup=build_inline_keyboard(
            keyboard=kbd
        ).as_markup()
    )


@router.callback_query(DeleteExceptionLogsCallback.filter())
async def delete_exception_logs(query: CallbackQuery) -> None:
    """
    Delete all exception logs.

    :param query:
    :return:
    """

    storage_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'logs',
                                'exceptions')
    logs = [log for log in os.listdir(storage_path) if log.endswith('.log')]

    if not logs:
        await query.answer(
            text=_('📜 No logs found.')
        )
        return

    for log in logs:
        file_path = os.path.join(storage_path, log)
        os.remove(file_path)

    await query.answer()

    await render_exception_logs(query.message)


@router.callback_query(DeleteExceptionLogCallback.filter())
async def delete_exception_log(query: CallbackQuery, callback_data: DeleteExceptionLogCallback) -> None:
    """
    Delete exception log.

    :param query:
    :param callback_data:
    :return:
    """

    log_file = callback_data.log

    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'storage', 'logs',
                             'exceptions', log_file)

    if not os.path.exists(file_path):
        await query.answer(
            text=_('📜 Log not found.')
        )
        return

    os.remove(file_path)

    await query.answer()

    await render_exception_logs(query.message)


@router.callback_query(PaginationCallback.filter())
async def paginate_logs(query: CallbackQuery, callback_data: PaginationCallback) -> None:
    """
    Handle pagination for logs.

    :param query: The CallbackQuery instance
    :param callback_data: The pagination callback data
    :return:
    """
    await query.answer()

    await render_exception_logs(query, page=callback_data.page)