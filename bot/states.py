from aiogram.fsm.state import State, StatesGroup

class BotStates(StatesGroup):
    waiting_for_keyword = State()
    waiting_for_list = State()
    waiting_for_url = State()
    waiting_for_manual_content = State()
    processing = State()
