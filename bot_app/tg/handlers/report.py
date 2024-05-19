from datetime import datetime, timedelta

from aiogram import F, Router, types, Bot
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, BufferedInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _, lazy_gettext as __
from aiogram3_calendar import DialogCalendar, dialog_cal_callback

from bot_app.modules import messages
from bot_app.tg.states.map import MapState
from bot_app.application.query_tool import QueryTool
from bot_app.application.builder import Builder
from bot_app.application.converter import change_data_format
from shared import settings

import logging

bot = Bot(
    token=settings.TELEGRAM_TOKEN,
    parse_mode=ParseMode.MARKDOWN_V2
    )

query_tool = QueryTool()
builder = Builder()
report_router = Router()


@report_router.callback_query(dialog_cal_callback.filter(), MapState.report)
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
            await start_report(callback_query.message, state)
        else:
            state_data['end'] = selected_date_str
            await state.set_data(state_data)
            await end_report(callback_query.message, state)
            

@report_router.message(Command(commands=['report']))
async def report(
    message: types.Message,
    state: FSMContext
):
    await message.answer(messages.CHANGE_MODE_MESSAGE.format('информационно\-отчетного документа'))
    await message.answer(
        messages.DATE_INPUT_MESSAGE,
        reply_markup=await DialogCalendar().start_calendar()
    )
    await state.set_state(MapState.report)


async def start_report(
    message: types.Message,
    state: FSMContext
):
    await message.delete()
    await bot.send_message(
        chat_id=message.chat.id,
        text=messages.DATE_INPUT_MESSAGE,
        reply_markup=await DialogCalendar().start_calendar()
    )
    
    
async def end_report(
    message: types.Message,
    state: FSMContext
):
    await message.delete()
    state_data = await state.get_data()
        
    data = await query_tool.get_data_by_dates(
        start_date=datetime.strptime(state_data['start'], '%Y-%m-%d').timestamp(),
        end_date=datetime.strptime(state_data['end'], '%Y-%m-%d').timestamp()
    )
    
    report_file, total_points = builder.report_creation(
        dataset=change_data_format(data),
        start_date=state_data['start'],
        end_date=state_data['end']
        )

    await bot.send_document(
        chat_id=message.chat.id,
        document=BufferedInputFile(
            file=report_file.getvalue(),
            filename='report.docx',
            ),
         caption=messages.MAP_CAPTION.format(
            'информационно\-отчетного документ',
            state_data['start'].replace('-', '\-'),
            state_data['end'].replace('-', '\-'),
            total_points       
        )
    )
    
    await state.clear()
    