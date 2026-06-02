import logging, random
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from database.crud import get_or_create_user, create_case, get_current_case, close_case, add_exp_and_money, add_dialog, get_dialog_history, get_case_type_for_level, ADMIN_IDS
from database.models import SessionLocal
from services.ai_service import generate_case, character_dialogue, evaluate_verdict
from .keyboards import main_menu_kb, case_menu_kb, interrogation_menu_kb, end_interrogation_kb, law_menu_kb, after_law_kb, new_case_kb, shop_kb
from .states import GameStates
from .law_texts import CRIMINAL_LAW, ADMIN_LAW, CIVIL_LAW
router = Router()
logger = logging.getLogger(__name__)
SHOP_ITEMS = {"buy_table": ("🪑 Новий стіл", 300), "buy_medal": ("🏅 Орден судді", 700), "buy_flag": ("🇺🇦 Прапор", 150)}
def profile_text(user):
    return f"⚖️ <b>Судовий кабінет</b>\n\n👤 Ваша Честе!\n🏅 Рівень: <b>{user.level}/30</b>\n⭐ Досвід: <b>{user.exp}/6</b>\n💰 Баланс: <b>{user.money} грн</b>\n\nЧим займемось сьогодні?"
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id, message.from_user.username)
        await state.set_state(GameStates.main_menu)
        greeting = "👑 <b>Адмін-режим активовано!</b>\n\n" if message.from_user.id in ADMIN_IDS else ""
        await message.answer(greeting + profile_text(user), reply_markup=main_menu_kb(), parse_mode="HTML")
    finally:
        db.close()
@router.message(Command("admin_max"))
async def cmd_admin_max(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id)
        user.level = 30
        user.money = 999999
        user.exp = 0
        db.commit()
        await message.answer("👑 Рівень 30, баланс 999999 грн активовано!")
    finally:
        db.close()
@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)
        await state.set_state(GameStates.main_menu)
        await callback.message.edit_text(profile_text(user), reply_markup=main_menu_kb(), parse_mode="HTML")
    finally:
        db.close()
    await callback.answer()
@router.callback_query(F.data == "take_case")
async def cb_take_case(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)
        existing = get_current_case(db, user)
        if existing:
            await state.set_state(GameStates.case_menu)
            await callback.message.edit_text(f"📂 <b>Поточна справа:</b>\n\n{existing.story}\n\n<i>Категорія: {existing.case_type}</i>", reply_markup=case_menu_kb(), parse_mode="HTML")
            await callback.answer()
            return
        available_types = get_case_type_for_level(user.level)
        case_type = random.choice(available_types)
        await callback.message.edit_text("⏳ Генерую нову справу...", parse_mode="HTML")
        data = await generate_case(case_type)
        create_case(db, user.user_id, case_type, data["story"], data["hidden_article"])
        await state.set_state(GameStates.case_menu)
        await callback.message.edit_text(f"📂 <b>Нова справа ({case_type}):</b>\n\n{data['story']}", reply_markup=case_menu_kb(), parse_mode="HTML")
    finally:
        db.close()
    await callback.answer()
@router.callback_query(F.data == "case_menu")
async def cb_case_menu(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)
        case = get_current_case(db, user)
        if not case:
            await callback.answer("Справи немає.", show_alert=True)
            return
        await state.set_state(GameStates.case_menu)
        await callback.message.edit_text(f"📂 <b>Справа ({case.case_type}):</b>\n\n{case.story}", reply_markup=case_menu_kb(), parse_mode="HTML")
    finally:
        db.close()
    await callback.answer()
@router.callback_query(F.data == "interrogation_menu")
async def cb_interrogation_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.interrogation_menu)
    await callback.message.edit_text("🗣 <b>Меню Допиту</b>\n\nКого бажаєте допитати?", reply_markup=interrogation_menu_kb(), parse_mode="HTML")
    await callback.answer()
@router.callback_query(F.data == "talk_accused")
async def cb_talk_accused(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.talking_accused)
    await callback.message.edit_text("👤 <b>Допит підсудного</b>\n\nПишіть ваше запитання.", reply_markup=end_interrogation_kb(), parse_mode="HTML")
    await callback.answer()
@router.callback_query(F.data == "talk_accuser")
async def cb_talk_accuser(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.talking_accuser)
    await callback.message.edit_text("👥 <b>Допит позивача/прокурора</b>\n\nПишіть ваше запитання.", reply_markup=end_interrogation_kb(), parse_mode="HTML")
    await callback.answer()
@router.message(GameStates.talking_accused)
async def msg_talk_accused(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id)
        case = get_current_case(db, user)
        if not case:
            await message.answer("Справа не знайдена.")
            return
        history = get_dialog_history(db, case.case_id, "підсудний")
        reply = await character_dialogue("Підсудний", case.story, history, message.text)
        add_dialog(db, case.case_id, "підсудний", "user", message.text)
        add_dialog(db, case.case_id, "підсудний", "assistant", reply)
        await message.answer(f"👤 <b>Підсудний:</b>\n{reply}", reply_markup=end_interrogation_kb(), parse_mode="HTML")
    finally:
        db.close()
@router.message(GameStates.talking_accuser)
async def msg_talk_accuser(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id)
        case = get_current_case(db, user)
        if not case:
            await message.answer("Справа не знайдена.")
            return
        history = get_dialog_history(db, case.case_id, "позивач")
        reply = await character_dialogue("Позивач / Прокурор", case.story, history, message.text)
        add_dialog(db, case.case_id, "позивач", "user", message.text)
        add_dialog(db, case.case_id, "позивач", "assistant", reply)
        await message.answer(f"👥 <b>Позивач:</b>\n{reply}", reply_markup=end_interrogation_kb(), parse_mode="HTML")
    finally:
        db.close()
@router.callback_query(F.data == "end_interrogation")
async def cb_end_interrogation(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.interrogation_menu)
    await callback.message.edit_text("🗣 <b>Меню Допиту</b>\n\nКого бажаєте допитати?", reply_markup=interrogation_menu_kb(), parse_mode="HTML")
    await callback.answer()
@router.callback_query(F.data == "law_menu")
async def cb_law_menu(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.law_menu)
    await callback.message.edit_text("📖 <b>Законодавство України</b>\n\nОберіть кодекс:", reply_markup=law_menu_kb(), parse_mode="HTML")
    await callback.answer()
@router.callback_query(F.data == "law_criminal")
async def cb_law_criminal(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(CRIMINAL_LAW, reply_markup=after_law_kb(), parse_mode="HTML")
    await callback.answer()
@router.callback_query(F.data == "law_admin")
async def cb_law_admin(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(ADMIN_LAW, reply_markup=after_law_kb(), parse_mode="HTML")
    await callback.answer()
@router.callback_query(F.data == "law_civil")
async def cb_law_civil(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(CIVIL_LAW, reply_markup=after_law_kb(), parse_mode="HTML")
    await callback.answer()
@router.callback_query(F.data == "verdict")
async def cb_verdict_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(GameStates.waiting_verdict)
    await callback.message.edit_text("🔨 <b>Винесення вердикту</b>\n\nНапишіть:\n• Чи винна особа\n• Яку статтю порушено\n• Яке покарання призначаєте\n\n<i>Введіть вирок у наступному повідомленні...</i>", parse_mode="HTML")
    await callback.answer()
@router.message(GameStates.waiting_verdict)
async def msg_verdict(message: Message, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, message.from_user.id)
        case = get_current_case(db, user)
        if not case:
            await message.answer("Справа не знайдена.")
            return
        await message.answer("⚖️ Передаю вирок на розгляд вищої інстанції...")
        result = await evaluate_verdict(case.story, case.correct_article, message.text)
        score = result.get("score", 2)
        feedback = result.get("feedback", "")
        if score == 3:
            exp_gain, money_gain = 3, 500
            header = "✅ <b>Чудова робота!</b> Вирок підтверджено!"
            reward_text = "<b>+3 EXP | +500 грн</b>"
        elif score == 2:
            exp_gain, money_gain = 1, 0
            header = "⚠️ <b>Справа неоднозначна.</b> Вирок прийнято з зауваженнями."
            reward_text = "<b>+1 EXP | +0 грн</b>"
        else:
            exp_gain, money_gain = 0, -300
            header = "❌ <b>Судова помилка!</b> Вирок скасовано. Штраф 300 грн."
            reward_text = "<b>+0 EXP | -300 грн</b>"
        result_data = add_exp_and_money(db, user, exp_gain, money_gain)
        close_case(db, user)
        level_up_text = f"\n\n🎉 <b>РІВЕНЬ ПІДВИЩЕНО до {result_data['new_level']}!</b>" if result_data["leveled_up"] else ""
        db.refresh(user)
        await state.set_state(GameStates.main_menu)
        await message.answer(f"{header}\n\n📋 <b>Розбір:</b>\n{feedback}\n\n{reward_text}{level_up_text}\n\n📊 Рівень {user.level} | {user.exp}/6 EXP | {user.money} грн", reply_markup=new_case_kb(), parse_mode="HTML")
    finally:
        db.close()
@router.callback_query(F.data == "shop")
async def cb_shop(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)
        await callback.message.edit_text(f"🛒 <b>Магазин покращень</b>\n\n💰 Баланс: <b>{user.money} грн</b>", reply_markup=shop_kb(), parse_mode="HTML")
    finally:
        db.close()
    await callback.answer()
@router.callback_query(F.data.in_({"buy_table", "buy_medal", "buy_flag"}))
async def cb_buy_item(callback: CallbackQuery, state: FSMContext):
    db = SessionLocal()
    try:
        user = get_or_create_user(db, callback.from_user.id)
        item_name, price = SHOP_ITEMS[callback.data]
        if user.money < price:
            await callback.answer(f"❌ Недостатньо грошей! Потрібно {price} грн.", show_alert=True)
            return
        user.money -= price
        db.commit()
        db.refresh(user)
        await callback.answer(f"✅ {item_name} придбано!", show_alert=True)
        await callback.message.edit_text(f"🛒 <b>Магазин покращень</b>\n\n💰 Баланс: <b>{user.money} грн</b>", reply_markup=shop_kb(), parse_mode="HTML")
    finally:
        db.close()
