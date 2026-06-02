from sqlalchemy.orm import Session
from .models import User, Case, DialogHistory
import os
ADMIN_IDS = [7245932902]
EXP_PER_LEVEL = 6
def get_or_create_user(db: Session, user_id: int, username: str = None) -> User:
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id, username=username)
        if user_id in ADMIN_IDS:
            user.level = 30
            user.money = 999999
            user.exp = 0
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
def add_exp_and_money(db: Session, user: User, exp: int, money: int) -> dict:
    user.exp += exp
    user.money += money
    leveled_up = False
    while user.exp >= EXP_PER_LEVEL and user.level < 30:
        user.exp -= EXP_PER_LEVEL
        user.level += 1
        leveled_up = True
    db.commit()
    db.refresh(user)
    return {"leveled_up": leveled_up, "new_level": user.level}
def create_case(db: Session, user_id: int, case_type: str, story: str, correct_article: str) -> Case:
    case = Case(user_id=user_id, case_type=case_type, story=story, correct_article=correct_article)
    db.add(case)
    db.commit()
    db.refresh(case)
    user = db.query(User).filter(User.user_id == user_id).first()
    user.current_case_id = case.case_id
    db.commit()
    return case
def get_current_case(db: Session, user: User):
    if not user.current_case_id:
        return None
    return db.query(Case).filter(Case.case_id == user.current_case_id, Case.status == "active").first()
def close_case(db: Session, user: User):
    if user.current_case_id:
        case = db.query(Case).filter(Case.case_id == user.current_case_id).first()
        if case:
            case.status = "completed"
        user.current_case_id = None
        db.commit()
def add_dialog(db: Session, case_id: int, character_type: str, role: str, message: str):
    entry = DialogHistory(case_id=case_id, character_type=character_type, role=role, message_text=message)
    db.add(entry)
    db.commit()
def get_dialog_history(db: Session, case_id: int, character_type: str) -> list:
    rows = db.query(DialogHistory).filter(DialogHistory.case_id == case_id, DialogHistory.character_type == character_type).order_by(DialogHistory.id).all()
    return [{"role": r.role, "content": r.message_text} for r in rows]
def get_case_type_for_level(level: int) -> list:
    if level <= 5:
        return ["Адміністративна"]
    elif level <= 15:
        return ["Адміністративна", "Цивільна"]
    else:
        return ["Адміністративна", "Цивільна", "Кримінальна"]
