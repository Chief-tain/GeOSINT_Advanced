from aiogram import Router, types

from shared.telegram.callbacks.null import NullCallbackData

null_callback_router = Router()


@null_callback_router.callback_query(NullCallbackData.filter())
async def null_callback_handler(
    callback: types.CallbackQuery,
):
    await callback.answer()
