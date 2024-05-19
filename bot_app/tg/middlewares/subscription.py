from typing import Any, Awaitable, Callable, get_type_hints

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from motor.motor_asyncio import AsyncIOMotorCollection

from bot_app.application import SubscriptionService


class SubscriptionServiceMiddleware(BaseMiddleware):
    def __init__(self, collection: AsyncIOMotorCollection):
        self.collection = collection

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if SubscriptionService in data['_handler_dependencies']:
            session = data['_session']
            data['subscription_service'] = SubscriptionService(
                session=session,
                collection=self.collection
            )
        return await handler(event, data)
