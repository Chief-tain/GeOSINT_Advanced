from aiogram.fsm.state import State, StatesGroup


class Start(StatesGroup):
    way_choice = State()
    reading_name = State()
    way_choice_region = State()
    reading_region = State()
    reading_intonation = State()
