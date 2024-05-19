from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from shared.dbs.db_gateway_async import DatabaseGatewayAsync


class DBGatewayMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if DatabaseGatewayAsync in data['_handler_dependencies']:
            session = data['_session']
            data['db_gateway'] = DatabaseGatewayAsync(session=session)
        return await handler(event, data)
