from aiogram.fsm.state import State, StatesGroup


class StopState(StatesGroup):
    complaint = State()
