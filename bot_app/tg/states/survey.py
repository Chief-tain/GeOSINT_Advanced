from aiogram.fsm.state import State, StatesGroup


class Survey(StatesGroup):
    waiting_for_text = State()
    complaint = State()
