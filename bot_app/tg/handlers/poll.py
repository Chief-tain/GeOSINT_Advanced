from aiogram import Router, Bot, F
from aiogram.filters import Command, CommandObject
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from bot_app.application import UserService, RabbitService
from shared import settings


poll_router = Router()

POLL_CREATORS_ID_LIST = [138503110, 95396520, 181197834, 150897551]


@poll_router.message(Command(commands=['poll']))
async def get_poll_variants(
    message: Message,
    command: CommandObject,
    state: FSMContext,
):
    if message.from_user.id not in POLL_CREATORS_ID_LIST:
        return
    lines = [line for line in command.args.split('\n') if line]
    question = lines[0]
    options = lines[1:]
    await message.answer_poll(
        question=question,
        options=options,
        is_anonymous=True,
        is_closed=True,
        allows_multiple_answers=True,
    )
    await state.update_data({'poll_args': lines})
    await message.answer('Всё правильно?', reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Да, запускаем', callback_data='poll:start')],
        [InlineKeyboardButton(text='Нет, отменяем', callback_data='poll:cancel')],
    ]))


@poll_router.callback_query(F.data == 'poll:start')
async def start_poll(
    callback_query: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    user_service: UserService,
    rabbit_service: RabbitService,
):
    context_data = await state.get_data()
    poll_args = context_data.pop('poll_args', None)
    if not poll_args:
        return await callback_query.message.answer('Smth went wrong')
    question = poll_args[0]
    options = poll_args[1:]
    poll = await bot.send_poll(
        chat_id=settings.POLLS_CHANNEL_USERNAME,
        question=question,
        options=options,
        is_anonymous=True,
        allows_multiple_answers=True,
    )
    await state.set_data(context_data)
    users_ids = await user_service.get_all_active_users()
    for user_id in users_ids:
        await rabbit_service.forward(
            user_id=user_id,
            from_chat=settings.POLLS_CHANNEL_USERNAME,
            message_id=poll.message_id,
            bot_id=bot.id,
        )
    await callback_query.answer(text='Запущено', show_alert=True)
    await callback_query.message.delete_reply_markup()


@poll_router.callback_query(F.data == 'poll:cancel')
async def cancel_poll(callback_query: CallbackQuery, state: FSMContext):
    context_data = await state.get_data()
    context_data.pop('poll_args', None)
    await state.set_data(context_data)
    await callback_query.answer(text='Отменено', show_alert=True)
    await callback_query.message.delete_reply_markup()
