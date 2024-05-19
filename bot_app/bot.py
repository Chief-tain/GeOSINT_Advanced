import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import I18n
from aiogram.enums import ParseMode

from bot_app.tg import routers
from bot_app.modules.commands import set_bot_commands
from shared import settings

logging.getLogger().setLevel(logging.INFO)


async def main():
    
    logging.info('Starting...')

    dp = Dispatcher()

    for router in routers:
        dp.include_router(router)

    bot = Bot(
        token=settings.TELEGRAM_TOKEN,
        parse_mode=ParseMode.MARKDOWN_V2
        )

    logging.info('Starting polling...')
    
    await set_bot_commands(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
