from aiogram import F, Router, types
from aiogram.filters import Command

from bot_app.modules import messages


start_router = Router()


@start_router.message(Command(commands=['start']))
async def greetings(
    message: types.Message
    ):
    await message.answer(messages.START_MESSAGE)
    