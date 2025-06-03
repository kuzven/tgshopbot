from sqlalchemy import Column, Integer, String
from helpers.database import Base

class Question(Base):
    __tablename__ = "faq_question"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(255), nullable=False)
    answer = Column(String, nullable=False)
