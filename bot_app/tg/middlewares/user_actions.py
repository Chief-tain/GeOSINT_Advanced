import asyncio
import typing
from datetime import datetime
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from shared.models import UserAction


class UserActionsMiddleware(BaseMiddleware):
    CACHE_MAX_OBJECTS = 50

    def __init__(self, pool: async_sessionmaker):
        super().__init__()

        self.pool = pool
        self.user_action_objects_cache: typing.List[UserAction] = list()
        self.insert_lock = asyncio.Lock()

    async def insert_if_needed(self):
        async with self.insert_lock:
            if len(self.user_action_objects_cache) >= self.CACHE_MAX_OBJECTS:
                async with self.pool() as session:
                    await session.execute(
                        insert(
                            UserAction
                        ).values(
                            [
                                {
                                    'dt': user_action.dt,
                                    'user_id': user_action.user_id,
                                    'action_type': user_action.action_type,
                                    'action': user_action.action,
                                }
                                for user_action in self.user_action_objects_cache
                            ]
                        )
                    )
                    await session.commit()

                self.user_action_objects_cache.clear()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            if event.forward_from or event.chat.type != 'private' or (not event.text):
                return await handler(event, data)

            self.user_action_objects_cache.append(
                UserAction(
                    dt=datetime.now(),
                    user_id=event.from_user.id,
                    action_type='message',
                    action=event.text
                )
            )
        elif isinstance(event, CallbackQuery):
            if event.message.chat.type != 'private' or (not event.data):
                return await handler(event, data)

            self.user_action_objects_cache.append(
                UserAction(
                    dt=datetime.now(),
                    user_id=event.from_user.id,
                    action_type='callback',
                    action=event.data,
                )
            )
        else:
            return await handler(event, data)

        res = await handler(event, data)
        await self.insert_if_needed()
        return res
