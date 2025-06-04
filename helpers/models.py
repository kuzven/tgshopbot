from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text, DECIMAL
from helpers.database import Base
from settings.config import MEDIA_URL

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

class SubCategory(Base):
    __tablename__ = "shop_subcategory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey("shop_category.id"), nullable=False)

class Product(Base):
    __tablename__ = "shop_product"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("shop_subcategory.id"), nullable=False)
    image = Column(String(255), nullable=False)
