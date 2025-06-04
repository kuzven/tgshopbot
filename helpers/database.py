import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.future import select
from sqlalchemy.sql import text

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

async def add_to_cart(user_id, product_id, quantity):
    """
    Добавляет товар в корзину или обновляет количество, используя `id`, а не `telegram_id`.
    """
    async with async_session_maker() as session:
        logger.info(f"🔍 Получаем `id` для `telegram_id={user_id}`.")

        # Получаем `id` по `telegram_id`
        user_check_query = text("SELECT id FROM users_botuser WHERE telegram_id = :user_id")
        result = await session.execute(user_check_query, {"user_id": user_id})
        user_db_id = result.scalar()

        if not user_db_id:
            logger.error(f"Ошибка! `telegram_id={user_id}` не найден в `users_botuser`.")
            return  # Останавливаем выполнение

        await session.commit()
        session.expire_all()

        logger.info(f"`id={user_db_id}` найден! Используем его при обработке `shop_cart`.")

        # Проверяем, есть ли товар в `shop_cart`
        check_cart_query = text("""
        SELECT quantity FROM shop_cart WHERE user_id = :user_db_id AND product_id = :product_id
        """)
        result = await session.execute(check_cart_query, {"user_db_id": user_db_id, "product_id": product_id})
        existing_quantity = result.scalar()

        if existing_quantity:
            # Если товар уже есть, обновляем количество
            new_quantity = existing_quantity + quantity
            logger.info(f"Товар {product_id} уже в корзине, обновляем количество до {new_quantity}.")

            update_cart_query = text("""
            UPDATE shop_cart SET quantity = :new_quantity WHERE user_id = :user_db_id AND product_id = :product_id
            """)
            await session.execute(update_cart_query, {"new_quantity": new_quantity, "user_db_id": user_db_id, "product_id": product_id})
        else:
            # Если товара ещё нет, добавляем новую запись
            logger.info(f"Товар {product_id} отсутствует в корзине, добавляем новый.")

            insert_cart_query = text("""
            INSERT INTO shop_cart (user_id, product_id, quantity, added_at)
            VALUES (:user_db_id, :product_id, :quantity, NOW())
            """)
            await session.execute(insert_cart_query, {"user_db_id": user_db_id, "product_id": product_id, "quantity": quantity})

        await session.commit()
        logger.info(f"Товар {product_id} обработан для пользователя `id={user_db_id}`.")
