from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from bot_app.application import UserService
from bot_app.application.user.service import UserCreateRequest
from bot_app.tg.states.stop import StopState


class RegistrationMiddleware(BaseMiddleware):
    def __init__(self, pool: async_sessionmaker):
        self.pool = pool
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        state: FSMContext = data.get('state')

        if (await state.get_state()) == StopState.complaint:
            return await handler(event, data)

        # state_data = await state.get_data()
        # if 'locale' in state_data:
        #     return await handler(event, data)

        from_user = event.from_user
        async with self.pool() as session:
            user_service = UserService(session)
            await user_service.create_user(
                UserCreateRequest(
                    telegram_id=from_user.id,
                    username=from_user.username,
                    first_name=from_user.first_name,
                    last_name=from_user.last_name,
                    language_code=from_user.language_code,
                )
            )
            await session.commit()
        await state.update_data({'locale': from_user.language_code})
        return await handler(event, data)
