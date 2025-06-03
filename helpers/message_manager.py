import logging
from aiogram import Bot

logger = logging.getLogger(__name__)

# Словарь для хранения ID последнего сообщения
last_message = {}

async def delete_previous_message(bot: Bot, user_id: int):
    """
    Удаляет предыдущее сообщение пользователя, если оно есть.
    """
    if user_id in last_message:
        message_id = last_message[user_id]
        logger.info(f"Попытка удалить предыдущее сообщение: {message_id} для пользователя {user_id}")
        try:
            await bot.delete_message(chat_id=user_id, message_id=message_id)
            logger.info(f"Сообщение {message_id} успешно удалено")
        except Exception as e:
            logger.warning(f"Ошибка удаления сообщения {message_id}: {e}")

async def save_last_message(user_id: int, message):
    """
    Сохраняет ID последнего отправленного сообщения.
    """
    if message and hasattr(message, "message_id"):
        last_message[user_id] = message.message_id
        logger.info(f"Сохранен ID нового сообщения: {message.message_id} для пользователя {user_id}")
