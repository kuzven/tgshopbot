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

async def delete_all_previous_messages(bot: Bot, user_id: int):
    """Удаляет ВСЕ предыдущие сообщения пользователя перед загрузкой новых товаров."""
    if user_id in last_message:
        message_ids = last_message[user_id]
        logger.info(f"Попытка удалить ВСЕ предыдущие сообщения: {message_ids} для пользователя {user_id}")
        for message_id in message_ids:
            try:
                await bot.delete_message(chat_id=user_id, message_id=message_id)
                logger.info(f"Сообщение {message_id} успешно удалено")
            except Exception as e:
                logger.warning(f"Ошибка удаления сообщения {message_id}: {e}")
        last_message[user_id] = []  # Очищаем список сообщений

async def save_last_message(user_id: int, message):
    """Сохраняет ID последнего отправленного сообщения (в виде списка)."""
    if message and hasattr(message, "message_id"):
        if user_id not in last_message:
            last_message[user_id] = []
        last_message[user_id].append(message.message_id)  # Добавляем в список
        logger.info(f"Сохранен ID сообщения: {message.message_id} для пользователя {user_id}")

async def get_last_message_id(user_id: int):
    """
    Возвращает ID последнего сообщения пользователя, если оно есть.
    """
    return last_message.get(user_id, None)
