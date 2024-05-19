from math import ceil
from aiogram.utils.i18n import gettext as _
from aiogram.utils.keyboard import (InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, )

from bot_app.application import SubscribedChannel

from shared.telegram.callbacks.account import (
    ChannelData,
    LanguageData,
    PaginationData,
    ScheduleData,
    ReferralAddData,
    ReferralGetCodeData,
    TimeZoneData,
    ScheduleTypeData,
    ScheduleTypeBackData,
)
from shared.telegram.callbacks.null import NullCallbackData
from shared.schedule import ScheduleConstants, ScheduleTimeTypeEnum

from typing import List, Tuple, Dict


def main(locale: str = None, audio_preload_enabled: bool = False):
    keyboard = [
        [
            # (KeyboardButton(text=_('premium_button', locale=locale))),
            (KeyboardButton(text=_('change_schedule', locale=locale))),
            (KeyboardButton(text=_('change_time_zone', locale=locale))),
        ],
        [
            (KeyboardButton(text=_('change_name', locale=locale))),
            (KeyboardButton(text=_('change_language', locale=locale))),
        ],
        [
            (KeyboardButton(
                text=(
                    _('disable_audio_preload', locale=locale)
                    if audio_preload_enabled else
                    _('enable_audio_preload', locale=locale)
                ),
                locale=locale
            )),
            KeyboardButton(text=_('kb_referral'), locale=locale)
        ],
        [
            KeyboardButton(text=_('kb_stop_bot', locale=locale)),
        ],
        [
            (KeyboardButton(text=_('kb_main_menu', locale=locale))),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def language():
    keyboard = [
        [
            InlineKeyboardButton(
                text='🇷🇺 Русский',
                callback_data=LanguageData(language_code='ru').pack(),
            ),
            InlineKeyboardButton(
                text='🇺🇸 English',
                callback_data=LanguageData(language_code='en').pack(),
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard, resize_keyboard=True)


def keep_name():
    keyboard = [[KeyboardButton(text=_('keep_name'))]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def channels(
        *subscribed_channels: SubscribedChannel, limit: int = 3, offset: int = 0
):
    keyboard = []
    for channel in subscribed_channels[offset: offset + limit]:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=_('delete_channel') + ' ' + channel.title + ' ❌',
                    callback_data=ChannelData(
                        id=channel.id, username=channel.username
                    ).pack(),
                )
            ]
        )

    if len(subscribed_channels) > limit:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text='<',
                    callback_data=PaginationData(direction='prev').pack(),
                ),
                InlineKeyboardButton(
                    text=f'[{offset // limit + 1}/{ceil(len(subscribed_channels) / limit)}]',
                    callback_data=PaginationData(direction='keep').pack(),
                ),
                InlineKeyboardButton(
                    text='>',
                    callback_data=PaginationData(direction='next').pack(),
                ),
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def schedule_type():
    keyboard = [
        [
            InlineKeyboardButton(text='[0-12)', callback_data=ScheduleTypeData(type='day').pack()),
            InlineKeyboardButton(text='[12-24)', callback_data=ScheduleTypeData(type='night').pack()),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def schedule(
        current_schedule: Dict[str, List[Tuple[int, int, bool]]],
        time_ranges: List[str],
        schedule_type: str,
        locale: str = None,
        disable_sate: str = "❌",
        enable_state: str = "✅",
        none_state: str = "🔘",
):
    keyboard = []

    start_row = [
        InlineKeyboardButton(text=none_state, callback_data=NullCallbackData().pack())
    ]
    start_row.extend(
        [
            InlineKeyboardButton(
                text=time_range, callback_data=NullCallbackData().pack()
            )
            for time_range in time_ranges
        ]
    )

    keyboard.append(start_row)

    for day in ScheduleConstants.DAYS_OF_WEEK:
        row = [
            InlineKeyboardButton(
                text=_(day, locale=locale), callback_data=NullCallbackData().pack()
            )
        ]

        day_hours: List[Tuple[int, int, bool]] = current_schedule.get(day, [])

        row.extend(
            [
                InlineKeyboardButton(
                    text=enable_state if is_enable else disable_sate,
                    callback_data=ScheduleData(day=day,
                                               type=schedule_type,
                                               start_time_range=start_time_range,
                                               end_time_range=end_time_range).pack(),
                )
                for start_time_range, end_time_range, is_enable in day_hours
            ]
        )

        keyboard.append(row)

    schedule_type_enum: ScheduleTimeTypeEnum = ScheduleTimeTypeEnum.for_str(schedule_type)
    command_button = []

    if schedule_type_enum == ScheduleTimeTypeEnum.NIGHT:
        command_button.append(
            InlineKeyboardButton(
                text='<<',
                callback_data=ScheduleTypeData(type='day').pack(),
            )
        )

    command_button.append(
        InlineKeyboardButton(
            text=_('back_to_schedule_type', locale=locale),
            callback_data=ScheduleTypeBackData().pack()
        )
    )

    if schedule_type_enum == ScheduleTimeTypeEnum.DAY:
        command_button.append(
            InlineKeyboardButton(
                text='>>',
                callback_data=ScheduleTypeData(type='night').pack()
            )
        )

    keyboard.append(command_button)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def referral(locale: str = None):
    keyboard = [
        [
            InlineKeyboardButton(text=_('referral_code', locale=locale), callback_data=ReferralGetCodeData().pack()),
            InlineKeyboardButton(text=_('referral_add', locale=locale), callback_data=ReferralAddData().pack()),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def time_zone():
    keyboard = [
        [
            InlineKeyboardButton(text='-3', callback_data=TimeZoneData(direct=-3).pack()),
            InlineKeyboardButton(text='-1', callback_data=TimeZoneData(direct=-1).pack()),
            InlineKeyboardButton(text='+1', callback_data=TimeZoneData(direct=1).pack()),
            InlineKeyboardButton(text='+3', callback_data=TimeZoneData(direct=3).pack()),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)
