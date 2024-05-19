from aiogram.utils.i18n import gettext as _
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.telegram.callbacks.digest import ExpandedWebSearchData

def expanded_web_search_kb(user_query_hash: int):
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=_('expanded_search'),
                callback_data=ExpandedWebSearchData(
                user_query_hash=user_query_hash
            ).pack()
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)