from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
from dotenv import load_dotenv
from sqlalchemy.future import select

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Создаём движок PostgreSQL в асинхронном режиме
engine = create_async_engine(DATABASE_URL, future=True, echo=True)

# Создаём фабрику сессий
async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)

# Базовый класс для моделей
class Base(DeclarativeBase):
    pass

# Получение асинхронной сессии
async def get_session() -> AsyncSession:
    """
    Создаёт новую асинхронную сессию PostgreSQL.
    Открывает соединение с БД и автоматически закрывает после использования.
    Используется для выполнения SQL-запросов в асинхронном режиме.
    """
    async with async_session_maker() as session:
        yield session

async def get_questions():
    """
    Загружает список часто задаваемых вопросов из базы данных.
    Возвращает список объектов `Question`, содержащих `text` (вопрос) и `answer` (ответ).
    """
    from helpers.models import Question
    from sqlalchemy.future import select
    import logging

    logger = logging.getLogger(__name__)

    async with async_session_maker() as session:
        result = await session.execute(select(Question))
        questions = result.scalars().all()
        logger.info(f"Загружено {len(questions)} вопросов: {[q.text for q in questions]}")
        return questions
