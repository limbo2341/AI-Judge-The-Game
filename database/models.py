from sqlalchemy import Column, Integer, String, Text, BigInteger, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
DATABASE_URL = "sqlite:///./game.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
class Base(DeclarativeBase):
    pass
class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, nullable=True)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    money = Column(Integer, default=1000)
    current_case_id = Column(Integer, nullable=True)
class Case(Base):
    __tablename__ = "cases"
    case_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, index=True)
    case_type = Column(String)
    story = Column(Text)
    correct_article = Column(Text)
    status = Column(String, default="active")
class DialogHistory(Base):
    __tablename__ = "dialog_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, index=True)
    character_type = Column(String)
    role = Column(String)
    message_text = Column(Text)
def init_db():
    Base.metadata.create_all(bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
