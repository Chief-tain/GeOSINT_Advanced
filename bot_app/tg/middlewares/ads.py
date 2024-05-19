from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot_app.application.advertisement.service import AdsService


class AdsServiceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if AdsService in data['_handler_dependencies']:
            session = data['_session']
            data['ads_service'] = AdsService(session)
        return await handler(event, data)
