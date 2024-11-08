from aiogram import Router

from src.callbacks.main import EmptyCallback, DeleteMessageCallback

# Import routers.
from src.routes.home import router as home_router
from src.routes.faq import router as faq_router
from src.routes.advertisement import router as advertisement_router
from src.routes.category import router as category_router
from src.routes.language import router as language_router
from src.routes.exception_logs import router as exception_logs_router
from src.routes.statistic import router as statistic_router

router = Router()

# Apply routers.
router.include_routers(home_router)
router.include_routers(faq_router)
router.include_routers(advertisement_router)
router.include_routers(category_router)
router.include_routers(language_router)
router.include_routers(exception_logs_router)
router.include_routers(statistic_router)


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
