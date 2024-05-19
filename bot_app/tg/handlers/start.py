import asyncio
from urllib.parse import parse_qs

from aiogram import F, Router, types, Bot, html
from aiogram.filters import CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, CommandObject, StateFilter

from bot_app.modules import messages


start_router = Router()


@start_router.message(Command(commands=['start']))
async def greetings(
    message: types.Message
    ):
    await message.answer(messages.START_MESSAGE)
    