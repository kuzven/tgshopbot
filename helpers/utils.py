import os
import logging
import aiohttp

from dotenv import load_dotenv
from aiogram import types

from settings.config import GROUP_ID, CHANNEL_ID

logger = logging.getLogger(__name__)  # Создаём логгер
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def check_subscription(user_id):
    """
    Проверяет, подписан ли пользователь на канал и группу.
    
    Аргументы:
        user_id (int): Telegram ID пользователя.

    Возвращает:
        bool: True, если подписан. False, если нет.
    """
    async with aiohttp.ClientSession() as session:
        for chat_id in [GROUP_ID, CHANNEL_ID]:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember?chat_id={chat_id}&user_id={user_id}"
            async with session.get(url) as response:
                data = await response.json()
                logger.info(f"Ответ API для {chat_id}: {data}")  # Логируем ответ API

                if not data["ok"]:
                    return False  # Ошибка API - считаем, что не подписан
                
                status = data["result"]["status"]
                if status in ["left", "kicked"]:
                    return False  # Пользователь НЕ подписан
    
    return True  # Пользователь подписан на канал и группу
