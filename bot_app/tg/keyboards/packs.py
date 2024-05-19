from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardMarkup

from shared.models import ChannelPack
from shared.telegram.callbacks.null import NullCallbackData
from shared.telegram.callbacks.packs import PackData, PackNavigation, PackToList, PackSubscribeData


def packs_list_kb(packs: list[ChannelPack], offset: int = 0, limit: int = 10):
    prev_data = NullCallbackData() if offset == 0 else PackNavigation(offset=offset-limit, limit=limit)
    footer = [
        InlineKeyboardButton(
            text='<',
            callback_data=prev_data.pack()
        ),
        InlineKeyboardButton(
            text=str(offset // limit + 1),
            callback_data=NullCallbackData().pack()
        ),
        InlineKeyboardButton(
            text='>',
            callback_data=PackNavigation(offset=offset+limit, limit=limit).pack()
        ),
    ]
    inline_keyboard = []
    for pack in packs:
        text = pack.name + ' (' + str(len(pack.channels)) + ' ' + _('pack_channels_count') + ')'
        inline_keyboard.append([
            InlineKeyboardButton(
                text=text,
                callback_data=PackData(id=pack.id, offset=offset, limit=limit).pack()
            )
        ])
    inline_keyboard.append(footer)
    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)


def pack_kb(pack_id: int, back_offset: int, back_limit: int = 10):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=_('btn_pack_subscribe'), callback_data=PackSubscribeData(id=pack_id).pack())],
        [InlineKeyboardButton(
            text=_('btn_pack_back'),
            callback_data=PackToList(offset=back_offset, limit=back_limit).pack()
        )],
    ])
