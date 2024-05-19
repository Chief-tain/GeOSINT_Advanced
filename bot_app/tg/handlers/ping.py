from aiogram import Router, types, Bot
from aiogram.filters import Command

from bot_app.application import RabbitService

ping_router = Router()


@ping_router.message(Command(commands=['ping']))
@ping_router.channel_post(Command(commands=['ping']))
async def ping(message: types.Message, rabbit_service: RabbitService, bot: Bot):
    await rabbit_service.ping(
        user_id=message.chat.id,
        bot_id=bot.id,
    )
