from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, )

from shared import settings


def main():
    keyboard = [
        [
            KeyboardButton(text=_('kb_about')),
            KeyboardButton(text=_('kb_contact')),
        ],
        [
            KeyboardButton(text=_('kb_main_menu')),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )


def contact():
    keyboard = [
        [InlineKeyboardButton(text=_('contact'), url=f'https://t.me/{settings.TELEGRAM_CONTACT_USERNAME}')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
