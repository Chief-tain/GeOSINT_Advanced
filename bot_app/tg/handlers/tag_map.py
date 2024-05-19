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
tag_map_router = Router()


@tag_map_router.callback_query(dialog_cal_callback.filter(), MapState.tag_map)
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
            await start_tag_map(callback_query.message, state)
        else:
            state_data['end'] = selected_date_str
            await state.set_data(state_data)
            await end_tag_map(callback_query.message, state)
            

@tag_map_router.message(Command(commands=['tag_map']))
async def start_tag_map(
    message: types.Message,
    state: FSMContext
):
    await message.answer(messages.CHANGE_MODE_MESSAGE.format('интерактивной карты по тегам'))
    await message.answer(messages.TAG_INPUT_MESSAGE)
    await state.set_state(MapState.tag_map)
    
    
@tag_map_router.message(MapState.tag_map)
async def tag_map(
    message: types.Message,
    state: FSMContext
):
    state_data = await state.get_data()
    state_data['tag_word'] = message.text
    await state.set_data(state_data)
    
    await message.answer(
        messages.DATE_INPUT_MESSAGE,
        reply_markup=await DialogCalendar().start_calendar()
    )


async def start_tag_map(
    message: types.Message,
    state: FSMContext
):
    await message.delete()
    await bot.send_message(
        chat_id=message.chat.id,
        text=messages.DATE_INPUT_MESSAGE,
        reply_markup=await DialogCalendar().start_calendar()
    )
    
    
async def end_tag_map(
    message: types.Message,
    state: FSMContext
):
    await message.delete()
    state_data = await state.get_data()
        
    data = await query_tool.get_data_by_dates(
        start_date=datetime.strptime(state_data['start'], '%Y-%m-%d').timestamp(),
        end_date=datetime.strptime(state_data['end'], '%Y-%m-%d').timestamp()
    )
    
    start_map, total_points, tag_words = builder.tag_map_creation(
        dataset=change_data_format(data),
        tag_word=state_data['tag_word'])
    
    await bot.send_message(
        chat_id=message.chat.id,
        text=messages.TOTAL_TAGS_MESSAGE.format(
            state_data['tag_word'],
            ', '.join(tag_words)
        )
    )

    await bot.send_document(
        chat_id=message.chat.id,
        document=BufferedInputFile(
            file=start_map.getvalue(),
            filename='tag_map.html',
            ),
        caption=messages.TAG_MAP_CAPTION.format(
            'тематическая интерактивная карта',
            state_data['tag_word'].replace('-', '\-'),
            state_data['start'].replace('-', '\-'),
            state_data['end'].replace('-', '\-'),
            total_points
        )
    )
    
    await state.clear()
    