from __future__ import annotations

from typing import Any, Awaitable, Callable

import aio_pika
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot_app.application.survey.service import SurveyService


class SurveyMiddleware(BaseMiddleware):
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
        if SurveyService not in data['_handler_dependencies']:
            return await handler(event, data)
        connection = await aio_pika.connect_robust(self.url)
        channel = await connection.channel()
        session = data['_session']
        data['survey_service'] = SurveyService(
            session=session,
            channel=channel,  # noqa
            queue=self.queue,
        )
        response = await handler(event, data)
        await connection.close()
        return response
