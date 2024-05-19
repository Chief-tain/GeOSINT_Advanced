from aiogram.utils.i18n import gettext as _
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_kb():
    keyboard = [
        [
            KeyboardButton(text=_('main_kb_instant_news'))
        ],
        [
            KeyboardButton(text=_('my_channels')),
            KeyboardButton(text=_('search_submenu')),
        ],
        [
            KeyboardButton(text=_('main_kb_account')),
            KeyboardButton(text=_('main_kb_help')),
            KeyboardButton(text=_('main_kb_donate')),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
