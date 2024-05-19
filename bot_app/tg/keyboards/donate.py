from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def donate_placeholder():
    keyboard = [
        [
            InlineKeyboardButton(
                text=_('tip_our_command'),
                url='https://t.me/espressonewsabout/7'
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
