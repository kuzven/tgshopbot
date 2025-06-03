from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from helpers.database import Base
from datetime import datetime

class BotUser(Base):
    __tablename__ = "users_botuser"

    telegram_id = Column(BigInteger, primary_key=True, autoincrement=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Question(Base):
    __tablename__ = "faq_question"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(255), nullable=False)
    answer = Column(String, nullable=False)

class Category(Base):
    __tablename__ = "shop_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
