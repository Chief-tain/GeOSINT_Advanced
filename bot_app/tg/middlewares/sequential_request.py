from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from aiogram.fsm.context import FSMContext
from aiogram.dispatcher.flags import get_flag
from aiogram.utils.i18n import gettext as _

import logging


class SequentialRequestMiddleware(BaseMiddleware):
    """
    Middleware for handling sequential requests. This middleware checks if a web search is in progress
    and prevents further requests until the current search is completed. This is useful to prevent
    simultaneous requests that could lead to data inconsistency or overloading the server.
    """

    ENABLE_SEQUENTIAL_REQUEST: str = 'enable_sequential_request'
    KEY_SEQUENTIAL_REQUEST: str = 'key_sequential_request'

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        message: Message,
        data: dict[str, Any]
    ) -> Any:
        enable_sequential_request: bool = get_flag(data, self.ENABLE_SEQUENTIAL_REQUEST, default=False)

        if not enable_sequential_request:
            return await handler(message, data)

        key_sequential_request: str = get_flag(data, self.KEY_SEQUENTIAL_REQUEST)
        state: FSMContext = data.get('state')

        user_data: Dict[str, Any] = await state.get_data()
        web_search_in_progress: bool = user_data.get(key_sequential_request, False)

        if web_search_in_progress:
            await message.answer(_('waiting_message'))
            logging.info(f'Attempt to access {key_sequential_request} prevented due to ongoing web search.')
            return False

        await state.update_data({key_sequential_request: True})

        try:
            handler_continue = await handler(message, data)
        except Exception as error:
            await state.update_data({key_sequential_request: False})
            raise error

        await state.update_data({key_sequential_request: False})

        return handler_continue
