import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Создаём движок PostgreSQL в асинхронном режиме
engine = create_async_engine(DATABASE_URL, future=True, echo=True)

# Создаём фабрику сессий
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

async def save_user(user):
    """
    Проверяет, есть ли пользователь в БД.
    Если нет – добавляет его в таблицу users_botuser.
    """
    from helpers.models import BotUser

    telegram_id = user.id
    first_name = user.first_name
    last_name = user.last_name if user.last_name else ""
    username = user.username if user.username else ""

    async with async_session_maker() as session:
        result = await session.execute(select(BotUser).where(BotUser.telegram_id == telegram_id))
        existing_user = result.scalar()
        
        if not existing_user:
            new_user = BotUser(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                created_at=datetime.utcnow()
            )
            session.add(new_user)
            await session.commit()
            logger.info(f"Новый пользователь сохранён: {first_name} {last_name} (@{username})")


async def get_questions():
    """
    Загружает список часто задаваемых вопросов из базы данных.
    Возвращает список объектов `Question`, содержащих `text` (вопрос) и `answer` (ответ).
    """
    from helpers.models import Question

    async with async_session_maker() as session:
        result = await session.execute(select(Question))
        questions = result.scalars().all()
        logger.info(f"Загружено {len(questions)} вопросов: {[q.text for q in questions]}")
        return questions
    
async def get_categories(limit=5, offset=0):
    """
    Загружает список категорий из таблицы shop_category.
    """
    from helpers.models import Category
    async with async_session_maker() as session:
        result = await session.execute(select(Category).limit(limit).offset(offset))
        return result.scalars().all()

async def get_subcategories(category_id, limit=5, offset=0):
    """
    Загружает список подкатегорий для заданной категории.
    """
    from helpers.models import SubCategory

    async with async_session_maker() as session:
        result = await session.execute(
            select(SubCategory).where(SubCategory.category_id == category_id).limit(limit).offset(offset)
        )
        return result.scalars().all()

async def get_products(subcategory_id, page=1):
    """
    Загружает список товаров для подкатегории с учетом пагинации.
    """
    from helpers.models import Product
    from settings.config import PRODUCTS_PER_PAGE

    offset = (page - 1) * PRODUCTS_PER_PAGE

    async with async_session_maker() as session:
        result = await session.execute(
            select(Product)
            .where(Product.subcategory_id == subcategory_id)
            .limit(PRODUCTS_PER_PAGE)
            .offset(offset)
        )
        products = result.scalars().all()

        logger.info(f"Загружено {len(products)} товаров для подкатегории {subcategory_id}, страница {page}")
        return products
