from aiogram.utils.i18n import gettext as _
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, KeyboardButtonRequestChat


def search_kb():
    keyboard = [
        [
            KeyboardButton(text=_('channels_browser')),
            KeyboardButton(text=_('channels_search')),
        ],
        [
            KeyboardButton(
                text=_('share_channel'),
                request_chat=KeyboardButtonRequestChat(
                    request_id=0,
                    chat_is_channel=True,
                    chat_has_username=True
                )
            ),
            KeyboardButton(text=_('channel_packs'))
        ],
        [
            KeyboardButton(text=_('kb_main_menu'))
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )
