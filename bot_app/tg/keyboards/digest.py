from aiogram.utils.i18n import gettext as _
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from shared.telegram.callbacks.digest import ExpandedSearchData

def expanded_search_kb(summary_id: int):
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=_('expanded_search'),
                callback_data=ExpandedSearchData(
                summary_id=summary_id
            ).pack()
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)