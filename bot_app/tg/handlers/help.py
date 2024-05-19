from aiogram import F, Router, types
from aiogram.filters import Command

from bot_app.modules import messages


help_router = Router()


@help_router.message(Command(commands=['help']))
async def get_help(message: types.Message):
    await message.answer(messages.HELP_MESSAGE)
    
    
@help_router.message(Command(commands=['region_list']))
async def get_help(message: types.Message):
    await message.answer(messages.REGION_LIST_MESSAGE)