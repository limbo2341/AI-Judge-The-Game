from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⚖️ Взяти нову справу", callback_data="take_case")],[InlineKeyboardButton(text="🛒 Магазин покращень", callback_data="shop")]])
def case_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🗣 Почати допит", callback_data="interrogation_menu")],[InlineKeyboardButton(text="📖 Законодавство України", callback_data="law_menu")],[InlineKeyboardButton(text="🔨 Винести вердикт", callback_data="verdict")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]])
def interrogation_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👤 Допитати підсудного", callback_data="talk_accused")],[InlineKeyboardButton(text="👥 Допитати позивача/прокурора", callback_data="talk_accuser")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="case_menu")]])
def end_interrogation_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🛑 Завершити допит", callback_data="end_interrogation")]])
def law_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔴 Кримінальний кодекс", callback_data="law_criminal")],[InlineKeyboardButton(text="🔵 Адміністративний кодекс", callback_data="law_admin")],[InlineKeyboardButton(text="🟢 Цивільний кодекс", callback_data="law_civil")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="case_menu")]])
def after_law_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад до кодексів", callback_data="law_menu")]])
def new_case_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔄 Почати нове діло", callback_data="take_case")],[InlineKeyboardButton(text="🏠 Головне меню", callback_data="main_menu")]])
def shop_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🪑 Новий стіл (+5% EXP) — 300 грн", callback_data="buy_table")],[InlineKeyboardButton(text="🏅 Орден судді (+10% EXP) — 700 грн", callback_data="buy_medal")],[InlineKeyboardButton(text="🇺🇦 Прапор (+2% EXP) — 150 грн", callback_data="buy_flag")],[InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu")]])
