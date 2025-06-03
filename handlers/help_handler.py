from aiogram import Router, types
from aiogram.filters import Command
from helpers.message_manager import delete_previous_message, save_last_message

router = Router()

@router.message(Command("help"))
async def help_handler(message: types.Message):
    """
    Обработчик команды /help.
    Ответы на частозадаваемые вопросы.
    """
    user_id = message.from_user.id
    # Удаляем предыдущее сообщение, если оно есть
    await delete_previous_message(message.bot, user_id)

    # Объявляем переменную sent_message
    sent_message = None  

    sent_message = await message.answer("Я могу подсказать, что тебя интересует. Введи свой вопрос.")

    # Сохраняем ID последнего отправленного сообщения
    await save_last_message(user_id, sent_message)