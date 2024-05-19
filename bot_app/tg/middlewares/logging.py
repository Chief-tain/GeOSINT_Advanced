from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, ChatMemberUpdated
from structlog import BoundLogger


class LoggingMiddleware(BaseMiddleware):
    def __init__(self, logger: BoundLogger):
        self.base_logger = logger
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            event_logger = self.base_logger.bind(
                type='message',
                event_id=event.message_id,
                user=event.from_user.id
            )
            event_logger.info('New message', text=event.text)
        elif isinstance(event, CallbackQuery):
            event_logger = self.base_logger.bind(
                type='callback',
                event_id=event.id,
                user=event.from_user.id
            )
            event_logger.info('New callback', data=event.data)
        elif isinstance(event, ChatMemberUpdated):
            event_logger = self.base_logger.bind(
                type='chatmember',
                status=event.new_chat_member.status,
                user=event.from_user.id
            )
            event_logger.info('Membership updated')
        else:
            event_logger = self.base_logger.bind(
                user=event.from_user.id
            )
        data['logger'] = event_logger
        return await handler(event, data)
