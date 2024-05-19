from aiogram.fsm.state import State, StatesGroup


class PackState(StatesGroup):
    read_pack_name = State()
    read_pack_id = State()
    read_channel_username = State()
    read_pack_source = State()
