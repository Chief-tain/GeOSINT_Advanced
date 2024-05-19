from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats


async def set_bot_commands(bot: Bot):
    data = [
        (
            [
                BotCommand(command='start', description="Начало работы"),
                BotCommand(command='help', description="Описание режимов работы"),
                BotCommand(command='map', description="Режим создания карты"),
                BotCommand(command='tag_map', description="Режим создания карты по тегам"),
                BotCommand(command='city_summary', description="Режим создания краткой новостной сводки по населенному пункту"),
                BotCommand(command='report', description="Режим создания информационно-отчетного документа")
            ],
            BotCommandScopeAllPrivateChats(),
            None
        )
    ]

    for commands_list, commands_scope, language in data:
        await bot.set_my_commands(commands=commands_list, scope=commands_scope, language_code=language)