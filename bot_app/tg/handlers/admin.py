from datetime import timezone, timedelta
import datetime
import logging
import uuid
import re

from aiogram import Router, types, Bot, F
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from pydantic import BaseModel, ValidationError
from structlog import BoundLogger

from bot_app.application import UserService, RabbitService, PackService
from bot_app.application.survey.service import SurveyService
from bot_app.application.advertisement.service import AdsService, AdvertisementCreateTmp, AdvertisementCreateRequest
from shared.telegram.callbacks.surveys import SurveySettings, SurveySettingAction
from bot_app.tg.states.survey import Survey
from bot_app.tg.states.packs import PackState
from bot_app.tg.states.ads import AdsState


admin_router = Router()

ADMIN_ID_LIST = [138503110, 95396520, 181197834]


class SurveySettingsDraft(BaseModel):
    text: str = 'Какую оценку ты мне поставишь?'
    count: int = 100
    with_subscriptions: bool = True
    exclude_recent: bool = False
    order: str = 'random'
    settings_message_id: int = 0


def render_text(settings: SurveySettingsDraft):
    text = 'Настройка опроса.\n'
    text += f'Текст: "{settings.text}"\n'
    text += f'Количество опрашиваемых: {settings.count}\n'
    filters = []
    if settings.with_subscriptions:
        filters.append('с подписками')
    if settings.exclude_recent:
        filters.append('без недавно опрошенных')
    if not filters:
        filters = 'нет'
    else:
        filters = ', '.join(filters)
    text += f'Фильтр опрашиваемых: {filters}\n'
    if settings.order == 'newest':
        order = 'сначала новые'
    elif settings.order == 'oldest':
        order = 'сначала старые'
    elif settings.order == 'random':
        order = 'случайная'
    else:
        order = 'неизвестная'
    text += f'Сортировка: {order}'
    return text


def render_markup(settings: SurveySettingsDraft):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text='Изменить текст',
            callback_data=SurveySettings(action=SurveySettingAction.EDIT_TEXT).pack()
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text='Уменьшить в 10 раз',
            callback_data=SurveySettings(action=SurveySettingAction.DIVIDE).pack()
        ),
        InlineKeyboardButton(
            text='Увеличить в 10 раз',
            callback_data=SurveySettings(action=SurveySettingAction.MULTIPLY).pack()
        ),
    )

    subs_button_text = '✓ С подписками' if settings.with_subscriptions else 'С подписками'
    recent_button_text = '✓ Без опрошенных' if settings.exclude_recent else 'Без опрошенных'
    builder.row(
        InlineKeyboardButton(
            text=subs_button_text,
            callback_data=SurveySettings(action=SurveySettingAction.SWITCH_SUB).pack()
        ),
        InlineKeyboardButton(
            text=recent_button_text,
            callback_data=SurveySettings(action=SurveySettingAction.EXCLUDE_RECENT).pack()
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text='Сначала новые',
            callback_data=SurveySettings(action=SurveySettingAction.ORDER_NEWEST).pack()
        ),
        InlineKeyboardButton(
            text='Сначала старые',
            callback_data=SurveySettings(action=SurveySettingAction.ORDER_OLDEST).pack()
        ),
        InlineKeyboardButton(
            text='Случайная',
            callback_data=SurveySettings(action=SurveySettingAction.ORDER_RANDOM).pack()
        ),
    )

    builder.row(
        InlineKeyboardButton(
            text='Запустить опрос',
            callback_data=SurveySettings(action=SurveySettingAction.START).pack()
        )
    )
    return builder.as_markup()


# def get_all_users_from_database(session: Session) -> list[int]:
#     stmt = select(User.id)
#     response = session.execute(stmt)
#     user_ids: list[int] = [row[0] for row in response.fetchall()]
#
#     return user_ids


@admin_router.message(Command(commands=['message_all']))
async def greetings(
    message: types.Message,
    bot: Bot,
    logger: BoundLogger,
    user_service: UserService,
    rabbit_service: RabbitService
):
    logger.info('User pressed /message_all')
    from_user = message.from_user
    if from_user.id not in ADMIN_ID_LIST:
        return

    text_to_send = message.html_text.replace('/message_all', '').strip()

    if not text_to_send:
        await bot.send_message(chat_id=from_user.id, text="Вы не ввели текст для рассылки.")
        return

    users_ids = await user_service.get_all_active_users()
    for user_id in users_ids:
        await rabbit_service.direct_message(user_id, text_to_send, bot.id)


# @admin_router.message(Command(commands=['survey']))
async def start_survey_setup(message: types.Message, state: FSMContext):
    blank_settings = SurveySettingsDraft()
    await state.update_data({'survey_settings': blank_settings.model_dump()})
    text = render_text(blank_settings)
    markup = render_markup(blank_settings)
    await message.answer(text, reply_markup=markup)


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.DIVIDE))
async def modify_survey_increase_count(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    if survey_settings.count <= 10:
        await callback.answer('Слишком мало людей для опроса')
        return
    survey_settings.count //= 10
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await callback.message.edit_text(text, reply_markup=markup)
    await state.update_data({'survey_settings': survey_settings.model_dump()})


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.MULTIPLY))
async def modify_survey_decrease_count(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    if survey_settings.count >= 10000:
        await callback.answer('Слишком много людей для опроса')
        return
    survey_settings.count *= 10
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await callback.message.edit_text(text, reply_markup=markup)
    await state.update_data({'survey_settings': survey_settings.model_dump()})


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.SWITCH_SUB))
async def modify_survey_switch_subscription_filter(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    survey_settings.with_subscriptions = not survey_settings.with_subscriptions
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await callback.message.edit_text(text, reply_markup=markup)
    await state.update_data({'survey_settings': survey_settings.model_dump()})


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.EXCLUDE_RECENT))
async def modify_survey_switch_exclude_recent_filter(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    survey_settings.exclude_recent = not survey_settings.exclude_recent
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await callback.message.edit_text(text, reply_markup=markup)
    await state.update_data({'survey_settings': survey_settings.model_dump()})


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.ORDER_NEWEST))
async def modify_survey_newest_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    survey_settings.order = 'newest'
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await callback.message.edit_text(text, reply_markup=markup)
    await state.update_data({'survey_settings': survey_settings.model_dump()})


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.ORDER_OLDEST))
async def modify_survey_oldest_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    survey_settings.order = 'oldest'
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await callback.message.edit_text(text, reply_markup=markup)
    await state.update_data({'survey_settings': survey_settings.model_dump()})


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.ORDER_RANDOM))
async def modify_survey_random_order(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    survey_settings.order = 'random'
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await callback.message.edit_text(text, reply_markup=markup)
    await state.update_data({'survey_settings': survey_settings.model_dump()})


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.EDIT_TEXT))
async def modify_survey_wait_for_text(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    survey_settings.settings_message_id = callback.message.message_id
    text = 'Введи новый текст для опроса:'
    await callback.message.edit_text(text, reply_markup=None)
    await state.update_data({'survey_settings': survey_settings.model_dump()})
    await state.set_state(Survey.waiting_for_text)


# @admin_router.message(Survey.waiting_for_text)
async def read_new_survey_text(message: types.Message, state: FSMContext, bot: Bot):
    new_text = message.text
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    survey_settings.text = new_text
    text = render_text(survey_settings)
    markup = render_markup(survey_settings)
    await bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=survey_settings.settings_message_id,
        reply_markup=markup
    )
    await state.update_data({'survey_settings': survey_settings.model_dump()})
    await state.set_state(None)
    await message.delete()


# @admin_router.callback_query(SurveySettings.filter(F.action == SurveySettingAction.START))
# @flags.survey
async def start_survey(callback: types.CallbackQuery, state: FSMContext, survey_service: SurveyService):
    await callback.answer()
    await callback.message.delete_reply_markup()
    context_data = await state.get_data()
    survey_settings = context_data.get('survey_settings')
    survey_settings = SurveySettingsDraft.model_validate(survey_settings)
    text = f'Опрос удовлетворённости на {survey_settings.count} человек отправлен'
    await callback.message.edit_text(text=text)
    await survey_service.start_survey(
        count=survey_settings.count,
        with_subscriptions=survey_settings.with_subscriptions,
        order=survey_settings.order,
        exclude_recent=survey_settings.exclude_recent,
        text=survey_settings.text,
    )


# @admin_router.callback_query(F.data.startswith('survey:'))
# @flags.survey
async def process_answer(
    callback: types.CallbackQuery,
    state: FSMContext,
    survey_service: SurveyService,
    user_service: UserService,
):
    await callback.message.delete_reply_markup()
    _, survey_id, rating = callback.data.split(':')
    survey_id = uuid.UUID(survey_id)
    rating = int(rating)
    await survey_service.register_vote(survey_id, callback.from_user.id, int(rating))
    text = callback.message.text
    text += f'\n— {rating}\n'
    text += '— Спасибо за ответ! '
    if rating > 3:
        subscription_info = await user_service.get_current_paid_subscription(telegram_id=callback.from_user.id)
        if subscription_info:
            await callback.message.edit_text(text)
            return
        text += 'Кстати, у нас есть подписочная система. '
        text += 'Посмотреть преимущества подписок можно в меню Настройки > Подписка.'
        await callback.message.edit_text(text)
        return
    text += 'Если не сложно, то опиши парой фраз, что именно не нравится, и я обязательно постараюсь стать лучше.'
    await callback.message.edit_text(text)
    await state.set_state(Survey.complaint)
    await state.update_data(
        {
            'complaint_till': (datetime.datetime.utcnow() + datetime.timedelta(minutes=20)).timestamp(),
            'survey_message_id': callback.message.message_id,
            'survey_message_text': text
        }
    )


# @admin_router.message(Survey.complaint)
# @flags.survey
async def read_complaint(message: types.Message, state: FSMContext, survey_service: SurveyService, bot: Bot):
    await state.set_state(None)
    context_data = await state.get_data()
    msg_id = context_data.get('survey_message_id')
    text = context_data.get('survey_message_text')
    if not msg_id or not text:
        await message.answer('Спасибо! Прямо сейчас я отправлю это сообщение своим разработчикам.')
    else:
        await message.delete()
        text += f'\n— {message.text[:500]}\n'
        text += '— Спасибо! Прямо сейчас я отправлю это сообщение своим разработчикам.'
        await bot.edit_message_text(text, chat_id=message.chat.id, message_id=msg_id)
    await survey_service.register_complaint(user_id=message.from_user.id, text=message.text)


@admin_router.message(Command(commands=['packs']), StateFilter(None))
async def enter_pack_mode(message: types.Message, command: CommandObject, pack_service: PackService, state: FSMContext):
    from_user = message.from_user
    if from_user.id not in ADMIN_ID_LIST:
        return
    if not command.args:
        packs = await pack_service.get_packs(author_id=message.from_user.id)
        if not packs:
            text = 'Наборов пока нет. Отправь название набора для начала:'
            await state.set_state(PackState.read_pack_name)
        else:
            text = ''
            for pack in packs:
                text += str(pack.id)
                text += ' '
                text += pack.name
                text += ' (каналов: '
                text += str(len(pack.channels))
                text += ')\n'
            text += '\nОтправь номер пака для начала редактирования'
            await state.set_state(PackState.read_pack_id)
        markup = types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text='Создать набор', callback_data='pack:create'),
            types.InlineKeyboardButton(text='Отмена', callback_data='pack:cancel'),
        ]])
        await message.answer(text=text, reply_markup=markup)
    else:
        pack = await pack_service.get_pack_channels(int(command.args))
        if not pack:
            return await message.answer('Нет такого пака')
        await state.update_data(
            {
                'pack_id': pack.id,
                'pack_channels': [channel.username for channel in pack.channels],
            }
        )
        if not pack:
            return await message.answer('Нет такого набора')
        text = str(pack.id) + ' ' + pack.name
        text += '\n\n'
        for channel in pack.channels:
            text += channel.username
            text += '\n'
        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text='Удалить набор', callback_data='pack:delete')],
                [types.InlineKeyboardButton(text='Готово', callback_data='pack:done')],
            ]
        )
        await state.set_state(PackState.read_channel_username)
        await message.answer(text, reply_markup=markup)


@admin_router.message(StateFilter(PackState.read_pack_name))
async def create_new_pack(message: types.Message, pack_service: PackService, state: FSMContext):
    new_pack_id = await pack_service.create_pack(message.text, message.from_user.id)
    await state.update_data({'pack_id': new_pack_id, 'pack_channels': []})
    await state.set_state(PackState.read_channel_username)
    text = str(new_pack_id) + ' ' + message.text
    text += 'source tag: —\nПубличный: False\n\n'
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Паблик', callback_data='pack:public')],
            [types.InlineKeyboardButton(text='Source', callback_data='pack:source')],
            [types.InlineKeyboardButton(text='Удалить набор', callback_data='pack:delete')],
            [types.InlineKeyboardButton(text='Готово', callback_data='pack:done')],
        ]
    )
    await message.answer(text=text, reply_markup=markup)


@admin_router.message(StateFilter(PackState.read_pack_id))
async def select_pack(message: types.Message, pack_service: PackService, state: FSMContext):
    pack_id = int(message.text)
    pack_info = await pack_service.get_pack_channels(pack_id=pack_id)
    if not pack_info:
        return await message.answer('Нет такого пака')
    if pack_info.author_id != message.from_user.id:
        return await message.answer('Это не твой пак')
    await state.update_data({
        'pack_id': pack_info.id,
        'pack_channels': [channel.username for channel in pack_info.channels],
    })
    await state.set_state(PackState.read_channel_username)
    text = f'{pack_info.id} {pack_info.name}\n'
    text += 'source tag: '
    text += pack_info.source if pack_info.source else '—'
    text += '\n'
    text += f'Публичный: {not pack_info.is_private}'
    text += '\n\n'
    for channel in pack_info.channels:
        text += channel.username
        text += '\n'
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Паблик', callback_data='pack:public')],
        [types.InlineKeyboardButton(text='Source', callback_data='pack:source')],
        [types.InlineKeyboardButton(text='Удалить набор', callback_data='pack:delete')],
        [types.InlineKeyboardButton(text='Готово', callback_data='pack:done')],
    ])
    await message.answer(text=text, reply_markup=markup)


@admin_router.message(StateFilter(PackState.read_channel_username))
async def manage_channels(message: types.Message, pack_service: PackService, state: FSMContext):
    channel_usernames = re.split(r'[ \n]', message.text)
    channel_usernames = [item.lstrip('@').replace('https://t.me/', '') for item in channel_usernames]
    context_data = await state.get_data()
    pack_id: int = context_data['pack_id']
    actual_channels: list[str] = context_data['pack_channels']
    for username in channel_usernames:
        if username in actual_channels:
            actual_channels.remove(username)
            await pack_service.remove_channel(pack_id=pack_id, channel_username=username)
        else:
            try:
                await pack_service.add_channel(pack_id=pack_id, channel_username=username)
            except Exception as err:
                await message.answer('Не получилось добавить канал ' + username)
            else:
                actual_channels.append(username)
    pack_info = await pack_service.get_pack_channels(pack_id=pack_id)
    await state.update_data({'pack_channels': actual_channels})
    text = f'{pack_info.id} {pack_info.name}\n'
    text += 'source tag: '
    text += pack_info.source if pack_info.source else '—'
    text += '\n'
    text += f'Публичный: {not pack_info.is_private}'
    text += '\n\n'
    for channel in pack_info.channels:
        text += channel.username
        text += '\n'
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Паблик', callback_data='pack:public')],
        [types.InlineKeyboardButton(text='Source', callback_data='pack:source')],
        [types.InlineKeyboardButton(text='Удалить набор', callback_data='pack:delete')],
        [types.InlineKeyboardButton(text='Готово', callback_data='pack:done')],
    ])
    await message.answer(text=text, reply_markup=markup)


@admin_router.callback_query(F.data == 'pack:delete')
async def delete_pack(callback: types.CallbackQuery, pack_service: PackService, state: FSMContext):
    context_data = await state.get_data()
    pack_id = context_data['pack_id']
    await callback.message.delete_reply_markup()
    await state.set_state(None)
    await pack_service.delete_pack(pack_id=pack_id)
    context_data.pop('pack_id')
    context_data.pop('pack_channels')
    await state.set_data(context_data)
    await callback.message.answer('Ок, удалено')


@admin_router.callback_query(F.data == 'pack:done')
async def pack_done(callback: types.CallbackQuery, state: FSMContext):
    context_data = await state.get_data()
    await callback.message.delete_reply_markup()
    await state.set_state(None)
    context_data.pop('pack_id')
    context_data.pop('pack_channels')
    await state.set_data(context_data)
    await callback.message.answer('Ок, закончили')


@admin_router.callback_query(F.data == 'pack:create')
async def pack_done(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await state.set_state(PackState.read_pack_name)
    await callback.message.answer('Отправь название нового набора')


@admin_router.callback_query(F.data == 'pack:cancel')
async def pack_done(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    await state.set_state(None)
    await callback.message.answer('Ок, закончили')


@admin_router.callback_query(F.data == 'pack:public')
async def pack_change_visibility(callback: types.CallbackQuery, pack_service: PackService, state: FSMContext):
    context_data = await state.get_data()
    pack_id: int = context_data['pack_id']
    pack_info = await pack_service.get_pack_channels(pack_id=pack_id)
    pack_info = await pack_service.update_pack_visibility(pack_id=pack_id, is_private=not pack_info.is_private)
    text = f'{pack_info.id} {pack_info.name}\n'
    text += 'source tag: '
    text += pack_info.source if pack_info.source else '—'
    text += '\n'
    text += f'Публичный: {not pack_info.is_private}'
    text += '\n\n'
    for channel in pack_info.channels:
        text += channel.username
        text += '\n'
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Паблик', callback_data='pack:public')],
        [types.InlineKeyboardButton(text='Source', callback_data='pack:source')],
        [types.InlineKeyboardButton(text='Удалить набор', callback_data='pack:delete')],
        [types.InlineKeyboardButton(text='Готово', callback_data='pack:done')],
    ])
    await callback.message.edit_text(text=text, reply_markup=markup)


@admin_router.callback_query(F.data == 'pack:source')
async def pack_edit_source(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        'Введи новый source',
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
            types.InlineKeyboardButton(text='Удалить source', callback_data='pack:source_remove')
        ]])
    )
    await callback.message.delete_reply_markup()
    await state.set_state(PackState.read_pack_source)


@admin_router.callback_query(F.data == 'pack:source_remove')
async def pack_remove_source(callback: types.CallbackQuery, pack_service: PackService, state: FSMContext):
    await callback.message.delete_reply_markup()
    context_data = await state.get_data()
    pack_id: int = context_data['pack_id']
    pack_info = await pack_service.update_pack_source(pack_id=pack_id, source=None)
    text = f'{pack_info.id} {pack_info.name}\n'
    text += 'source tag: '
    text += pack_info.source if pack_info.source else '—'
    text += '\n'
    text += f'Публичный: {not pack_info.is_private}'
    text += '\n\n'
    for channel in pack_info.channels:
        text += channel.username
        text += '\n'
    markup = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text='Паблик', callback_data='pack:public')],
            [types.InlineKeyboardButton(text='Source', callback_data='pack:source')],
            [types.InlineKeyboardButton(text='Удалить набор', callback_data='pack:delete')],
            [types.InlineKeyboardButton(text='Готово', callback_data='pack:done')],
        ]
    )
    await callback.message.answer(text=text, reply_markup=markup)
    await state.set_state(PackState.read_channel_username)


@admin_router.message(StateFilter(PackState.read_pack_source))
async def read_pack_source(message: types.Message, pack_service: PackService, state: FSMContext):
    context_data = await state.get_data()
    pack_id: int = context_data['pack_id']
    pack_info = await pack_service.update_pack_source(pack_id=pack_id, source=message.text)
    text = f'{pack_info.id} {pack_info.name}\n'
    text += 'source tag: '
    text += pack_info.source if pack_info.source else '—'
    text += '\n'
    text += f'Публичный: {not pack_info.is_private}'
    text += '\n\n'
    for channel in pack_info.channels:
        text += channel.username
        text += '\n'
    markup = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text='Паблик', callback_data='pack:public')],
        [types.InlineKeyboardButton(text='Source', callback_data='pack:source')],
        [types.InlineKeyboardButton(text='Удалить набор', callback_data='pack:delete')],
        [types.InlineKeyboardButton(text='Готово', callback_data='pack:done')],
    ])
    await message.answer(text=text, reply_markup=markup)
    await state.set_state(PackState.read_channel_username)


@admin_router.message(Command(commands=['ads']), StateFilter(None))
async def ads_start(message: types.Message, state: FSMContext):
    from_user = message.from_user
    if from_user.id not in ADMIN_ID_LIST:
        return
    await message.answer('Отправь тег кампании')
    await state.set_state(AdsState.read_tag)
    await state.update_data({'ad_tmp': {'author_id': message.from_user.id}})


@admin_router.message(StateFilter(AdsState.read_tag))
async def ads_read_tag(message: types.Message, state: FSMContext):
    context_data = await state.get_data()
    ad_tmp = context_data.get('ad_tmp')
    tag = message.text
    ad_tmp['tag'] = tag
    try:
        AdvertisementCreateTmp.model_validate(ad_tmp)
    except ValidationError as err:
        logging.error(err)
        await message.answer('Не, не получилось, попробуй снова')
    else:
        await state.update_data({'ad_tmp': ad_tmp})
        await state.set_state(AdsState.read_text)
        await message.answer('Отправь форматированный текст')


@admin_router.message(StateFilter(AdsState.read_text))
async def ads_read_text(message: types.Message, state: FSMContext):
    context_data = await state.get_data()
    ad_tmp = context_data.get('ad_tmp')
    text = message.html_text
    ad_tmp['text'] = text
    try:
        AdvertisementCreateTmp.model_validate(ad_tmp)
    except ValidationError as err:
        logging.error(err)
        await message.answer('Не, не получилось, попробуй снова')
    else:
        await state.update_data({'ad_tmp': ad_tmp})
        await state.set_state(AdsState.read_media)
        await message.answer(
            'Отправь ссылку (для превью; может быть ссылкой на медиа-файл)',
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text='Без ссылки', callback_data='ads:no_media')
            ]])
        )


@admin_router.callback_query(F.data == 'ads:no_media')
async def ads_no_media(callback: types.CallbackQuery, state: FSMContext):
    context_data = await state.get_data()
    ad_tmp = context_data.get('ad_tmp')
    ad_tmp['media'] = None
    await state.update_data({'ad_tmp': ad_tmp})
    await state.set_state(AdsState.read_start_date)
    await callback.message.answer('Отправь дату и время начала кампании (2000-01-01 00:00:00)')


@admin_router.message(StateFilter(AdsState.read_media))
async def ads_read_media(message: types.Message, state: FSMContext):
    context_data = await state.get_data()
    ad_tmp = context_data.get('ad_tmp')
    preview_link = message.text
    ad_tmp['media'] = preview_link
    try:
        AdvertisementCreateTmp.model_validate(ad_tmp)
    except ValidationError as err:
        logging.error(err)
        await message.answer('Не, не получилось, попробуй снова')
    else:
        await state.update_data({'ad_tmp': ad_tmp})
        await state.set_state(AdsState.read_start_date)
        await message.answer('Отправь дату и время начала кампании (2000-01-01 00:00:00)')


@admin_router.message(StateFilter(AdsState.read_start_date))
async def ads_read_start_date(message: types.Message, state: FSMContext):
    context_data = await state.get_data()
    ad_tmp = context_data.get('ad_tmp')
    timestamp = message.html_text
    try:
        timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=3)))
        ad_tmp['start_at'] = str(timestamp)
        AdvertisementCreateTmp.model_validate(ad_tmp)
    except ValidationError as err:
        logging.error(err)
        await message.answer('Не, не получилось, попробуй снова')
    else:
        await state.update_data({'ad_tmp': ad_tmp})
        await state.set_state(AdsState.read_end_date)
        await message.answer('Отправь дату и время окончания кампании (2000-01-01 00:00:00)')


@admin_router.message(StateFilter(AdsState.read_end_date))
async def ads_read_end_date(message: types.Message, state: FSMContext):
    context_data = await state.get_data()
    ad_tmp = context_data.get('ad_tmp')
    timestamp = message.html_text
    try:
        timestamp = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone(timedelta(hours=3)))
        ad_tmp['end_at'] = str(timestamp)
        AdvertisementCreateTmp.model_validate(ad_tmp)
    except ValidationError as err:
        logging.error(err)
        await message.answer('Не, не получилось, попробуй снова')
    else:
        await state.update_data({'ad_tmp': ad_tmp})
        await state.set_state(None)
        text = ad_tmp['text']
        text = f'From {ad_tmp["start_at"]}\nTo {ad_tmp["end_at"]}\n\n' + text
        markup = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [types.InlineKeyboardButton(text='Подтвердить', callback_data='ads:confirm')],
                [types.InlineKeyboardButton(text='Отменить', callback_data='ads:cancel')],
            ]
        )
        if ad_tmp['media']:
            link_preview = types.LinkPreviewOptions(is_disabled=False, url=ad_tmp['media'], show_above_text=True)
        else:
            link_preview = types.LinkPreviewOptions(is_disabled=True)
        await message.answer(text=text, reply_markup=markup, link_preview_options=link_preview)


@admin_router.callback_query(F.data == 'ads:confirm')
async def create_ad(callback: types.CallbackQuery, state: FSMContext, ads_service: AdsService):
    await callback.message.delete_reply_markup()
    context_data = await state.get_data()
    ad_tmp = context_data.get('ad_tmp')
    await ads_service.create_ad(AdvertisementCreateRequest.model_validate(ad_tmp))
    context_data.pop('ad_tmp')
    await state.set_data(context_data)
    await callback.answer('Создано', show_alert=True)


@admin_router.callback_query(F.data == 'ads:cancel')
async def cancel_ad(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete_reply_markup()
    context_data = await state.get_data()
    context_data.pop('ad_tmp', None)
    await state.set_data(context_data)
    await callback.answer('Отменено', show_alert=True)
