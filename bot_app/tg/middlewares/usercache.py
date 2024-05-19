from typing import Any, Awaitable, Callable
from datetime import timedelta, datetime

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker
import logging
from bot_app.application import UserService


class UserCacheMiddleware(BaseMiddleware):
    def __init__(self, pool: async_sessionmaker, expire_time: timedelta = timedelta(days=1)):
        self.pool = pool
        self.expire_time = expire_time
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get('event_from_user')
        if not user:
            return await handler(event, data)
        state: FSMContext = data['state']
        context_data = await state.get_data()
        complaint_till = context_data.get('complaint_till')
        if complaint_till and datetime.fromtimestamp(complaint_till) < datetime.utcnow():
            logging.info('Complaint time passed')
            await state.set_state(None)
            context_data.pop('complaint_till')
            await state.set_data(context_data)
        expires_at = context_data.get('cache_expires_at')
        keys = [context_data.get('locale'), context_data.get('premium')]
        are_keys_present = [key is not None for key in keys]
        if expires_at and (datetime.fromtimestamp(expires_at) > datetime.now()) and (all(are_keys_present)):
            return await handler(event, data)
        else:
            logging.info('Cache expired or some keys missing, updating')
            async with self.pool() as session:
                user_service = UserService(session=session)
                user_obj = await user_service.get_user(user_id=user.id)
                if user_obj:
                    subscription_obj = await user_service.get_current_paid_subscription(telegram_id=user.id)
                    if not subscription_obj:
                        premium_level = -1
                    else:
                        premium_level = subscription_obj.type.priority
                    new_data = {
                        'locale': user_obj.language_code,
                        'premium': premium_level,
                        'cache_expires_at': (datetime.now() + self.expire_time).timestamp()
                    }
                    await state.update_data(new_data)
            return await handler(event, data)
