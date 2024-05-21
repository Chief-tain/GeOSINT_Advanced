from bot_app.tg.handlers.help import help_router
from bot_app.tg.handlers.start import start_router
from bot_app.tg.handlers.map import map_router
from bot_app.tg.handlers.tag_map import tag_map_router
from bot_app.tg.handlers.report import report_router
from bot_app.tg.handlers.summary import summary_router
from bot_app.tg.handlers.total_summary import total_summary_router


routers = [
    start_router,
    help_router,
    map_router,
    tag_map_router,
    report_router,
    summary_router,
    total_summary_router
]


__all__ = (
    'start_router',
    'help_router',
    'map_router',
    'tag_map_router',
    'report_router',
    'summary_router',
    'total_summary_router'
)
