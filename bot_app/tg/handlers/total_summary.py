from datetime import datetime

from aiogram import F, Router, types, Bot
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram3_calendar import DialogCalendar, dialog_cal_callback

from bot_app.modules import messages
from bot_app.tg.states.map import MapState
from bot_app.application.query_tool import QueryTool
from bot_app.application.builder import Builder
from bot_app.application.converter import change_data_format
from shared import settings


bot = Bot(
    token=settings.TELEGRAM_TOKEN,
    parse_mode=ParseMode.MARKDOWN_V2
    )

query_tool = QueryTool()
builder = Builder()
total_summary_router = Router()


@total_summary_router.callback_query(dialog_cal_callback.filter(), MapState.total_summary)
async def process_dialog_calendar(
    callback_query: CallbackQuery,
    callback_data: CallbackData,
    state: FSMContext
):
    selected, date = await DialogCalendar().process_selection(
        callback_query, callback_data
    )

    if selected:
        state_data = await state.get_data()
        selected_date_str = date.strftime("%Y-%m-%d")
        
        if 'start' not in state_data:
            state_data['start'] = selected_date_str
            await state.set_data(state_data)
            await start_total_summary(callback_query.message, state)
        else:
            state_data['end'] = selected_date_str
            await state.set_data(state_data)
            await end_total_summary(callback_query.message, state)
            

@total_summary_router.message(Command(commands=['total_summary']))
async def map(
    message: types.Message,
    state: FSMContext
):
    await message.answer(messages.CHANGE_MODE_MESSAGE.format('общей информационно\-новостной сводки'))
    await message.answer(
        messages.DATE_INPUT_MESSAGE,
        reply_markup=await DialogCalendar().start_calendar()
    )
    await state.set_state(MapState.total_summary)


async def start_total_summary(
    message: types.Message,
    state: FSMContext
):
    await message.delete()
    await bot.send_message(
        chat_id=message.chat.id,
        text=messages.DATE_INPUT_MESSAGE,
        reply_markup=await DialogCalendar().start_calendar()
    )
    
    
async def end_total_summary(
    message: types.Message,
    state: FSMContext
):
    await message.delete()
    state_data = await state.get_data()
        
    data = await query_tool.get_data_by_dates(
        start_date=datetime.strptime(state_data['start'], '%Y-%m-%d').timestamp(),
        end_date=datetime.strptime(state_data['end'], '%Y-%m-%d').timestamp()
    )
    
    summary: str = await builder.total_summary_creation(
        dataset=change_data_format(data)
        )
    
    await bot.send_message(
        chat_id=message.chat.id,
        text=summary
    )
    
    await state.clear()
    