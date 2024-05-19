from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def greeting(locale: str):
    keyboard = [
        [
            KeyboardButton(text=_('setup_now', locale=locale)),
            KeyboardButton(text=_('setup_later', locale=locale)),
        ],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def ask_for_name():
    keyboard = [
        [InlineKeyboardButton(text=_('keep_name'), callback_data='keep_name')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def ask_for_region():
    keyboard = [
        [InlineKeyboardButton(text=_('none_region'), callback_data='none_region')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def captcha(locale: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("Yes", locale=locale))
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
