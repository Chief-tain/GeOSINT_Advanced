from aiogram.fsm.state import State, StatesGroup


class WebSearch(StatesGroup):
    web_search = State()