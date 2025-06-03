import logging
import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, Router
from aiogram.types import BotCommand
from aiogram.filters import Command

from helpers.utils import check_subscription
from helpers.message_manager import delete_previous_message, save_last_message
from settings.config import GROUP_ID, CHANNEL_ID
from handlers.start_handler import router as start_router
from handlers.faq_handler import router as faq_router
from handlers.catalog_handler import router as catalog_router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler("bot.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"),  # Логи сохраняются в файл размером до 5MB, храним 3 файла
        logging.StreamHandler()  # Логи выводятся в консоль
    ]
)

logger = logging.getLogger(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Подключаем хендлеры
dp.include_router(start_router)
dp.include_router(faq_router)
dp.include_router(catalog_router)

async def main():
    await bot.set_my_commands([  # Устанавливаем команды бота перед запуском
        BotCommand(command="start", description="Меню"),
        BotCommand(command="faq", description="FAQ")
    ])
    await dp.start_polling(bot)  # Запуск бота
    await bot.session.close()  # Корректное закрытие сессии

if __name__ == "__main__":
    try:
        asyncio.run(main())  # Запуск с автоматическим управлением событиями
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную")

