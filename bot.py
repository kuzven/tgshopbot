import logging
import asyncio
import os
import logging
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command

from helpers.utils import check_subscription
from settings.config import GROUP_ID, CHANNEL_ID

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

last_message = {}  # Словарь для хранения ID последнего сообщения пользователя

@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Обработчик команды /start.
    Проверяет подписку пользователя и отправляет приветственное сообщение.
    """
    user_id = message.from_user.id

    # Удаляем предыдущее сообщение, если оно есть
    if user_id in last_message:
        message_id = last_message[user_id]
        logger.info(f"Попытка удалить предыдущее сообщение: {message_id} для пользователя {user_id}")

        try:
            await bot.delete_message(chat_id=user_id, message_id=last_message[user_id])
            logger.info(f"Сообщение {message_id} успешно удалено")
        except Exception as e:
            logger.warning(f"Ошибка удаления сообщения {message_id}: {e}")

    is_subscribed = await check_subscription(user_id)
    
    # Объявляем переменную sent_message
    sent_message = None  

    if is_subscribed:
        sent_message = await message.answer("Привет 👋 Ты подписан на группу и канал, добро пожаловать в бот!")
    else:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔗 Подписаться на канал", url="https://t.me/tgshop_channel")],
            [types.InlineKeyboardButton(text="🔗 Подписаться на группу", url="https://t.me/+n-qLN2T8xCZlOTEy")]
        ])
        sent_message = await message.answer("❗ Ты не подписан на наш канал и группу! Для использования бота подпишись по кнопкам ниже, затем нажми /start чтобы проверить подписку!", reply_markup=keyboard)

    # Сохраняем ID последнего отправленного сообщения
    if sent_message is not None:
        last_message[user_id] = sent_message.message_id
        logger.info(f"Сохранен ID нового сообщения: {sent_message.message_id} для пользователя {user_id}")

@dp.message(Command("help"))
async def help_handler(message: types.Message):
    """
    Обработчик команды /help.
    Ответы на частозадаваемые вопросы.
    """
    await message.answer("Я могу подсказать, что тебя интересует. Введи свой вопрос.")

async def main():
    await dp.start_polling(bot)  # Запуск бота
    await bot.session.close()  # Корректное закрытие сессии

if __name__ == "__main__":
    try:
        asyncio.run(main())  # Запуск с автоматическим управлением событиями
    except KeyboardInterrupt:
        logging.info("Бот остановлен вручную")

