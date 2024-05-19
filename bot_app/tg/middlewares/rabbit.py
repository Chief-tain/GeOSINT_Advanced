from typing import Any, Awaitable, Callable

import aio_pika
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot_app.application import RabbitService


class RabbitMiddleware(BaseMiddleware):
    def __init__(self, amqp_url: str, queue: str):
        self.url = amqp_url
        self.queue = queue
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        connection = await aio_pika.connect_robust(self.url)
        channel = await connection.channel()
        data['rabbit_service'] = RabbitService(channel, self.queue)  # NOQA
        response = await handler(event, data)
        await connection.close()
        return response
