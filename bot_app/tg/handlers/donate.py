from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

import bot_app.tg.keyboards.donate as kb

donate_router = Router()


@donate_router.message(Command(commands=['donate']))
@donate_router.message(F.text == __('main_kb_donate'))
async def donate_placeholder(message: types.Message):
    await message.answer(_('gratitude_message'))
    await message.answer(
        _('donate_message'), reply_markup=kb.donate_placeholder()
    )
