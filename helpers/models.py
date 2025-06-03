from sqlalchemy import Column, Integer, String
from helpers.database import Base

class Question(Base):
    __tablename__ = "faq_question"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(255), nullable=False)
    answer = Column(String, nullable=False)

class Category(Base):
    __tablename__ = "shop_category"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
