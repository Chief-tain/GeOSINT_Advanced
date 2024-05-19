from aiogram import F, Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.i18n import gettext as _, lazy_gettext as __

import bot_app.tg.keyboards.account as kb
from bot_app.application import (SubscriptionService, UserService, PackService, ScheduleTextService)
from shared.telegram.callbacks.account import (
    ChannelData,
    LanguageData,
    PaginationData,
    ScheduleData,
    ReferralAddData,
    ReferralGetCodeData,
    TimeZoneData,
    ScheduleTypeBackData,
    ScheduleTypeData,
)
from bot_app.tg.keyboards.common import main_kb
from bot_app.tg.states.account import (
    Account,
    Referral,
)
from shared.schedule import ScheduleService, ScheduleTimeTypeEnum
from shared.settings import SERVER_TIME_ZONE_NAME
from time_zone import TimeZoneConstant

account_router = Router()


@account_router.message(Command(commands=['settings']))
@account_router.message(F.text == __('main_kb_account'))
async def help_menu(message: types.Message, user_service: UserService):
    await message.answer(
        _('to_account'),
        reply_markup=kb.main(
            audio_preload_enabled=await user_service.get_audio_preload_setting_state(message.from_user.id)
        )
    )


@account_router.message(F.text == __('change_language'))
async def change_language(message: types.Message):
    await message.answer(_('ask_for_language'), reply_markup=kb.language())


@account_router.callback_query(LanguageData.filter())
async def read_language(
    callback: types.CallbackQuery,
    callback_data: LanguageData,
    state: FSMContext,
    user_service: UserService,
):
    locale = callback_data.language_code
    await callback.answer(locale)
    await user_service.update_language(
        telegram_id=callback.from_user.id, language_code=locale
    )
    await state.update_data({'locale': locale})
    await callback.message.answer(
        _('language_set', locale=locale),
        reply_markup=kb.main(
            locale=locale,
            audio_preload_enabled=await user_service.get_audio_preload_setting_state(callback.from_user.id),
        )
    )


@account_router.message(F.text == __('enable_audio_preload'))
async def enable_audio_preload(
    message: types.Message,
    user_service: UserService,
):
    await user_service.change_audio_preload_setting(message.from_user.id, True)

    await message.answer(
        _('enabled_audio_preload'), reply_markup=kb.main(audio_preload_enabled=True),
    )


@account_router.message(F.text == __('disable_audio_preload'))
async def enable_audio_preload(
    message: types.Message,
    user_service: UserService,
):
    await user_service.change_audio_preload_setting(message.from_user.id, False)

    await message.answer(
        _('disabled_audio_preload'), reply_markup=kb.main(),
    )


@account_router.message(F.text == __('change_name'))
async def change_name(message: types.Message, state: FSMContext):
    await message.answer(_('ask_for_new_name'), reply_markup=kb.keep_name())
    await state.set_state(Account.reading_name)


@account_router.message(F.text == __('keep_name'), Account.reading_name)
async def keep_name(message: types.Message, state: FSMContext, user_service: UserService):
    first_name = message.from_user.first_name
    text = _('new_name_accepted {first_name}')
    text = text.format(first_name=first_name)
    await message.answer(
        text,
        reply_markup=kb.main(
            audio_preload_enabled=await user_service.get_audio_preload_setting_state(message.from_user.id)
        )
    )
    await state.set_state()


@account_router.message(Account.reading_name)
async def read_name(
    message: types.Message, state: FSMContext, user_service: UserService
):
    new_name = message.text
    await user_service.update_name(
        telegram_id=message.from_user.id,
        first_name=new_name,
    )
    text = _('new_name_accepted {first_name}')
    text = text.format(first_name=new_name)
    await message.answer(
        text,
        reply_markup=kb.main(
            audio_preload_enabled=await user_service.get_audio_preload_setting_state(message.from_user.id)
        ),
    )
    await state.set_state()


@account_router.message(F.text == __('kb_main_menu'))
async def return_to_main_menu(message: types.Message):
    await message.answer(_('to_main_menu'), reply_markup=main_kb())


@account_router.message(F.text == __('my_channels'))
async def show_channels(
    message: types.Message,
    state: FSMContext,
    subscription_service: SubscriptionService,
):
    channels = await subscription_service.get_subscriptions(
        message.from_user.id
    )
    if not channels:
        await message.answer(_('no_subscribed_channels'))
        await state.update_data({'channels': []})
        return
    await state.update_data({'channels': channels, 'limit': 3, 'offset': 0})
    await message.answer(
        _('channel_list'),
        reply_markup=kb.channels(*channels)
    )


@account_router.callback_query(PaginationData.filter())
async def channel_navigation(
    callback: types.CallbackQuery,
    callback_data: PaginationData,
    state: FSMContext
):
    await callback.answer()
    data = await state.get_data()
    offset = data['offset']
    limit = data['limit']
    channels = data['channels']
    if callback_data.direction == 'prev':
        if offset == 0:
            return
        offset -= limit
        await state.update_data({'offset': offset})
        await callback.message.edit_reply_markup(
            reply_markup=kb.channels(*channels, offset=offset)
        )
    if callback_data.direction == 'next':
        if offset + limit >= len(channels):
            return
        offset += limit
        await state.update_data({'offset': offset})
        await callback.message.edit_reply_markup(
            reply_markup=kb.channels(*channels, offset=offset)
        )


@account_router.callback_query(ChannelData.filter())
async def unsubscribe_from_channel(
    callback: types.CallbackQuery,
    callback_data: ChannelData,
    state: FSMContext,
    subscription_service: SubscriptionService,
):
    await callback.answer()
    data = await state.get_data()
    offset = data['offset']
    limit = data['limit']
    channels = data['channels']
    channels = [
        channel
        for channel in channels
        if channel.id != callback_data.id
    ]
    await subscription_service.unsubscribe(
        user_id=callback.from_user.id,
        channel_username=callback_data.username
    )
    if len(channels) == 0:
        await callback.message.delete_reply_markup()
        await callback.message.edit_text(_('no_subscribed_channels'))
        return
    if len(channels) <= offset:
        offset -= limit
    await state.update_data({'offset': offset, 'channels': channels})
    await callback.message.edit_reply_markup(
        reply_markup=kb.channels(*channels, offset=offset)
    )


@account_router.message(F.text == __('change_schedule'))
async def ask_for_schedule_type(message: types.Message):
    await message.answer(
        text=_('choose_new_schedule_type'),
        reply_markup=kb.schedule_type()
    )


@account_router.callback_query(ScheduleTypeBackData.filter())
async def ask_for_schedule_type_back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text=_('choose_new_schedule_type'),
        reply_markup=kb.schedule_type()
    )


@account_router.callback_query(ScheduleTypeData.filter())
async def ask_for_schedule_type_keyboard(
        callback: types.CallbackQuery,
        schedule_service: ScheduleService,
        user_service: UserService,
        state: FSMContext,
        callback_data: ScheduleTypeData
):
    data = await state.get_data()
    locale: str = data.get('locale')
    user_id: int = callback.from_user.id

    schedule_time_type: str = callback_data.type

    user_time_zone: int = (await user_service.get_user(user_id=user_id)).time_zone
    server_time_zone: int = TimeZoneConstant.TIME_ZONE_BY_NAME[SERVER_TIME_ZONE_NAME]

    await schedule_service.load_digest_hours_with_utc_offset(
        user_id=user_id,
        offset=user_time_zone - server_time_zone
    )

    await callback.message.edit_text(
        text=_('choose_new_schedule'),
        reply_markup=kb.schedule(
            current_schedule=schedule_service.get_days_interval(ScheduleTimeTypeEnum.for_str(schedule_time_type)),
            time_ranges=schedule_service.get_intervals(ScheduleTimeTypeEnum.for_str(schedule_time_type)),
            locale=locale,
            schedule_type=schedule_time_type
        )
    )


@account_router.callback_query(ScheduleData.filter())
async def change_schedule(
    callback: types.CallbackQuery,
    callback_data: ScheduleData,
    schedule_service: ScheduleService,
    state: FSMContext,
    user_service: UserService
):
    await callback.answer()

    data = await state.get_data()
    locale: str = data.get('locale')
    premium = data.get('premium') != -1
    user_id: int = callback.from_user.id

    start_schedule_interval: int = callback_data.start_time_range
    end_schedule_interval: int = callback_data.end_time_range
    schedule_time_type: str = callback_data.type

    user_time_zone: int = (await user_service.get_user(user_id=user_id)).time_zone
    server_time_zone: int = TimeZoneConstant.TIME_ZONE_BY_NAME[SERVER_TIME_ZONE_NAME]

    await schedule_service.load_digest_hours_with_utc_offset(
        user_id=user_id,
        offset=user_time_zone-server_time_zone
    )

    is_remove, updated_digest_hours = schedule_service.update(
        start_interval=start_schedule_interval,
        end_interval=end_schedule_interval
    )

    is_acceptable_schedule: bool = ScheduleService.is_acceptable_schedule(
        digest_hours=updated_digest_hours,
        is_premium=premium
    )

    if is_remove or is_acceptable_schedule:
        schedule_service.set_digest_hours(updated_digest_hours)
        await callback.message.edit_reply_markup(
            reply_markup=kb.schedule(
                current_schedule=schedule_service.get_days_interval(ScheduleTimeTypeEnum.for_str(schedule_time_type)),
                time_ranges=schedule_service.get_intervals(ScheduleTimeTypeEnum.for_str(schedule_time_type)),
                locale=locale,
                schedule_type=schedule_time_type
            )
        )

        updated_digest_hours = ScheduleService.shift_digest_hours(
            digest_hours=updated_digest_hours,
            offset=server_time_zone-user_time_zone
        )
        await schedule_service.save_digest_hours(digest_hours=updated_digest_hours)

        return

    text = 'Так часто -- только на тарифах Silver и Gold. Сменить тариф можно в Настройки -> Подписка.'
    await callback.message.answer(text=text)


@account_router.message(F.text == __('kb_referral'))
async def referral_keyboard(message: types.Message):
    await message.answer(_('referral_message'), reply_markup=kb.referral())


@account_router.callback_query(ReferralAddData.filter())
async def referral_add(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Referral.reading_name)
    await callback.message.edit_text(text=_('referral_add_message'))


@account_router.message(Referral.reading_name)
async def referral_add(
    message: types.Message,
    state: FSMContext,
    user_service: UserService,
):
    await state.set_state()

    referral_id_str: str = message.text

    if not referral_id_str.isdigit():
        await message.answer(_('referral_bad_code'))
        await message.answer(_('referral_message'), reply_markup=kb.referral())
        return

    referral_id: int = int(referral_id_str)
    user_id: int = message.from_user.id

    if referral_id == user_id:
        await message.answer(_('referral_of_yourself'))
        await message.answer(_('referral_message'), reply_markup=kb.referral())
        return

    referral_user = await user_service.get_user(referral_id)
    if referral_user is None:
        await message.answer(_('referral_not_exist'))
        await message.answer(_('referral_message'), reply_markup=kb.referral())
        return

    user = await user_service.get_user(user_id)
    if user.referral_id is not None:
        await message.answer(_('referral_already_added'))
        await message.answer(_('referral_message'), reply_markup=kb.referral())
        return

    await message.answer(
        text=_('referral_successfully_added').format(user_name=referral_user.username)
    )

    await message.bot.send_message(
        chat_id=referral_id,
        text=_('referral_successfully_added_by_your_code').format(user_name=user.username)
    )

    await user_service.set_user_referral(user_id, referral_id)


@account_router.callback_query(ReferralGetCodeData.filter())
async def referral_get_code(
    callback: types.CallbackQuery,
    pack_service: PackService,
    subscription_service: SubscriptionService,
    bot: Bot,
):
    rid = callback.from_user.id
    payload = f'rid={rid}'
    start_link = await create_start_link(bot, payload, encode=True)
    text: str = _('referral_code_message {rid} {deeplink}').format(rid=rid, deeplink=start_link)

    subscriptions = await subscription_service.get_subscriptions(user_id=rid)
    channel_usernames = [channel.username for channel in subscriptions]
    current_packs = await pack_service.get_packs(author_id=rid)
    for pack in current_packs:
        await pack_service.delete_pack(pack.id)
    new_pack_id = await pack_service.create_pack(f'RID{rid}', author_id=rid, source=str(rid))
    for username in channel_usernames:
        await pack_service.add_channel(new_pack_id, username)

    await callback.message.edit_text(
        text=text,
        reply_markup=kb.referral(),
        parse_mode='HTML'
    )


@account_router.message(F.text == __('change_time_zone'))
async def time_zone_keyboard(message: types.Message, user_service: UserService, state: FSMContext):
    user = await user_service.get_user(user_id=message.from_user.id)
    data = await state.get_data()
    locale: str = data.get('locale')

    await message.answer(
        text=ScheduleTextService.get_time_zone_message(user.time_zone, locale),
        reply_markup=kb.time_zone()
    )


@account_router.callback_query(TimeZoneData.filter())
async def change_time_zone(
    callback: types.CallbackQuery,
    callback_data: TimeZoneData,
    schedule_service: ScheduleService,
    user_service: UserService,
    state: FSMContext
):
    await callback.answer()

    user_id: int = callback.from_user.id

    current_time_zone: int = (await user_service.get_user(user_id=user_id)).time_zone
    direct_time_zone: int = callback_data.direct
    updated_time_zone: int = current_time_zone + direct_time_zone

    if updated_time_zone < -12 or updated_time_zone > 14:
        await callback.message.answer(_('invalid_time_zone'))
        return

    await schedule_service.load_digest_hours(user_id=user_id)
    current_digest_hours: list[int] = schedule_service.get_digest_hours()
    updated_digest_hours: list[int] = ScheduleService.shift_digest_hours(
        digest_hours=current_digest_hours,
        offset=-direct_time_zone
    )

    await schedule_service.save_digest_hours(digest_hours=updated_digest_hours)
    await user_service.update_time_zone(telegram_id=user_id, time_zone=updated_time_zone)

    data = await state.get_data()
    locale: str = data.get('locale')

    await callback.message.edit_text(
        text=ScheduleTextService.get_time_zone_message(updated_time_zone, locale),
        reply_markup=kb.time_zone()
    )
