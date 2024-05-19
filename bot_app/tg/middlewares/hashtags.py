from typing import Any, Awaitable, Callable, get_type_hints

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot_app.application.hasgtags.hashtags import HashtagApp


class HashtagAppMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if HashtagApp in data['_handler_dependencies']:
            session = data['_session']
            data['hashtag_app'] = HashtagApp(session)
        return await handler(event, data)
