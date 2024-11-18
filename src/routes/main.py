from aiogram import Router

from src.callbacks.main import EmptyCallback, DeleteMessageCallback

# Import routers.
from src.routes import routers

router = Router()

for r in routers:
    router.include_router(r)


@router.callback_query(EmptyCallback.filter())
async def empty_callback(query: EmptyCallback) -> None:
    """
    Empty callback.
    """

    await query.answer()


@router.callback_query(DeleteMessageCallback.filter())
async def delete_message_callback(query: DeleteMessageCallback, callback_data: DeleteMessageCallback) -> None:
    """
    Delete message callback.
    """

    try:
        await query.answer()
        await query.bot.delete_message(
            chat_id=query.message.chat.id,
            message_id=callback_data.message_id
        )
    except Exception as e:
        print(e)
        # await home(query)
