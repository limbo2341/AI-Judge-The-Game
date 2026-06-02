from aiogram.fsm.state import State, StatesGroup
class GameStates(StatesGroup):
    main_menu = State()
    case_menu = State()
    interrogation_menu = State()
    talking_accused = State()
    talking_accuser = State()
    waiting_verdict = State()
    law_menu = State()
