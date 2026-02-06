from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    waiting_for_keyword = State()
    waiting_for_list = State()
    processing = State()
