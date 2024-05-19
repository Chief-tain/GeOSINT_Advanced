import asyncio
from datetime import datetime
from functools import wraps

from aiogram import types
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.i18n import gettext as _


def follow_min_timestamp_callback(
        callback_data_kwarg_name: str = 'callback_data',
        min_timestamp_field_name: str = 'min_timestamp',
):
    def inner(func):
        @wraps(func)
        async def wrap(*args, **kwargs):
            if callback_data_kwarg_name not in kwargs:
                return await func(*args, **kwargs)

            callback_data = kwargs[callback_data_kwarg_name]

            if not isinstance(callback_data, CallbackData):
                return await func(*args, **kwargs)

            callback_data_dict = callback_data.model_dump()

            if min_timestamp_field_name not in callback_data_dict:
                return await func(*args, **kwargs)

            min_timestamp = callback_data_dict[min_timestamp_field_name]

            if not min_timestamp:
                return await func(*args, **kwargs)

            secs_to_wait = min_timestamp - int(datetime.utcnow().timestamp())

            if secs_to_wait <= 0:
                return await func(*args, **kwargs)

            callback = next(filter(lambda arg: isinstance(arg, types.CallbackQuery), args), None)

            if callback:
                await callback.answer(
                    _('Action will be possible in {secs_to_wait} secs').format(secs_to_wait=secs_to_wait)
                )

            await asyncio.sleep(secs_to_wait)

            return await func(*args, **kwargs)
        return wrap
    return inner
