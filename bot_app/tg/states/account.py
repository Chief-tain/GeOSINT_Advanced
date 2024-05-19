from aiogram.fsm.state import State, StatesGroup


class Account(StatesGroup):
    reading_name = State()

class Referral(StatesGroup):
    reading_name = State()
