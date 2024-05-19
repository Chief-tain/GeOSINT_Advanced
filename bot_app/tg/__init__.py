# from bot_app.tg.handlers.account import account_router
# from bot_app.tg.handlers.admin import admin_router
# from bot_app.tg.handlers.browser import channels_browser_router
# from bot_app.tg.handlers.digest import digest_router
# from bot_app.tg.handlers.donate import donate_router
# from bot_app.tg.handlers.forward import forward_router
from bot_app.tg.handlers.help import help_router
# from bot_app.tg.handlers.null_callback import null_callback_router
# from bot_app.tg.handlers.ping import ping_router
from bot_app.tg.handlers.start import start_router
from bot_app.tg.handlers.map import map_router
from bot_app.tg.handlers.tag_map import tag_map_router
# from bot_app.tg.handlers.block import block_router
# from bot_app.tg.handlers.stop import stop_router
# from bot_app.tg.handlers.search import search_router
# from bot_app.tg.handlers.subscribe import subscribe_router
# from bot_app.tg.handlers.subscribe import subscribe_router
# from bot_app.tg.handlers.web_search import web_search_router
# from bot_app.tg.handlers.premium import premium_router
# from bot_app.tg.handlers.poll import poll_router


routers = [
    # premium_router,
    # poll_router,
    # digest_router,
    start_router,
    help_router,
    map_router,
    tag_map_router,
    # account_router,
    # forward_router,
    # donate_router,
    # admin_router,
    # ping_router,
    # block_router,
    # stop_router,
    # channels_browser_router,
    # subscribe_router,
    # search_router,
    # web_search_router,
    # null_callback_router,
]


__all__ = (
    # 'routers',
    # 'donate_router',
    'start_router',
    'help_router',
    'map_router',
    'tag_map_router',
    # 'account_router',
    # 'forward_router',
    # 'digest_router',
    # 'admin_router',
    # 'block_router',
    # 'stop_router',
    # 'search_router',
    # 'subscribe_router',
    # 'channels_browser_router',
    # 'ping_router',
    # 'null_callback_router',
)
