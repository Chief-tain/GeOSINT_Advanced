import asyncio
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import Message


class MediaGroupsMiddleware(BaseMiddleware):
    KEY_TO_SAVE_LAST_MEDIA_GROUP_ID = 'last_media_group_id'

    def __init__(self):
        self._redis_lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[Message, dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: dict[str, Any],
    ) -> Any:
        if not await self.is_next_message_in_media_group(message, data):
            return await handler(message, data)

    async def is_next_message_in_media_group(self, message: Message, data: dict[str, Any]):
        # will work only with RedisStorageCustomKeys as FSM's storage

        if not message.media_group_id:
            return False

        storage_key = StorageKey(
            user_id=user.id if (user := data.get("event_from_user")) else None,
            chat_id=chat.id if (chat := data.get("event_chat")) else None,
            bot_id=data['bot'].id,
            thread_id=data.get("event_thread_id"),
        )

        async with self._redis_lock:
            last_media_group_id = \
                await data['dispatcher'].storage.get_custom_key(
                    storage_key, self.KEY_TO_SAVE_LAST_MEDIA_GROUP_ID)

            if last_media_group_id != message.media_group_id:
                await data['dispatcher'].storage.set_custom_key(
                    storage_key, self.KEY_TO_SAVE_LAST_MEDIA_GROUP_ID, message.media_group_id)

                return False

            return True
