from src.routes.home import router as home_router
from src.routes.faq import router as faq_router
from src.routes.advertisement import router as advertisement_router
from src.routes.category import router as category_router
from src.routes.language import router as language_router
from src.routes.exception_logs import router as exception_logs_router
from src.routes.statistic import router as statistic_router
from src.routes.admin import router as admin_router
from src.routes.user_advertisements import router as user_advertisements_router
from src.routes.edit_advertisement import router as edit_router
from src.routes.req_advertisements import router as req_advertisements_router
from src.handlers.advertisement import router as handle_advertisement_router

routers = [
    home_router,
    faq_router,
    advertisement_router,
    category_router,
    language_router,
    exception_logs_router,
    statistic_router,
    admin_router,
    user_advertisements_router,
    edit_router,
    req_advertisements_router,
    handle_advertisement_router
]