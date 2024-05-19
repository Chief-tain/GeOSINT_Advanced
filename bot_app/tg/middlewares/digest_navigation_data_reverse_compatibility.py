from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery

from shared.telegram.callbacks.digest import OldDigestNavigationData, DigestNavigationData


class DigestNavigationDataReverseCompatibility(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        callback_query: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(callback_query, CallbackQuery) and \
                (filter_result := await OldDigestNavigationData.filter()(callback_query)):
            callback_query = callback_query.model_copy(
                update={'data': DigestNavigationData(**filter_result['callback_data'].dict(), page_number=1).pack()},
            )

        return await handler(callback_query, data)
