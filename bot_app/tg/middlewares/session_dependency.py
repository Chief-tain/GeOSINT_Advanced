from typing import Any, Awaitable, Callable, get_type_hints

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.dispatcher.flags import get_flag
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker


class PostgresqlSessionMiddleware(BaseMiddleware):
    def __init__(self, pool: async_sessionmaker):
        self.pool = pool
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data['_handler_dependencies'] = get_type_hints(data['handler'].callback).values()
        is_using_postgres = get_flag(data, 'is_using_postgres')
        if not is_using_postgres:
            return await handler(event, data)
        async with self.pool() as session:
            data['_session'] = session
            try:
                response = await handler(event, data)
            except SQLAlchemyError as err:
                await session.rollback()
                raise err
            else:
                await session.commit()
            return response
