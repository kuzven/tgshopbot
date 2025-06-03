from aiogram import Router, types
from aiogram.filters import Command
from helpers.message_manager import delete_previous_message, save_last_message

router = Router()

# @router.callback_query(lambda callback_query: callback_query.data == "faq")
# async def faq_handler(callback_query: types.CallbackQuery):
#     """
#     Обработчик кнопки FAQ.
#     Показывает часто задаваемые вопросы в формате инлайн режима с автоматическим дополнением вопроса.
#     """
#     user_id = callback_query.from_user.id

#     # Удаляем предыдущее сообщение, если оно есть
#     await delete_previous_message(callback_query.message.bot, user_id)

#     faq_text = """❓ **Ответы на частозадаваемые вопросы**:
    
#     📦 **Как посмотреть каталог?**  
#     Используйте кнопку "📦 Каталог" в меню.

#     🛒 **Как работает корзина?**  
#     Добавьте товары в корзину и перейдите в "🛒 Корзина", чтобы оформить заказ.

#     💳 **Как оплатить?**  
#     Доступны разные способы оплаты. Подробнее в разделе **FAQ**.

#     Если у вас есть другие вопросы, напишите их здесь!"""
    
#     sent_message = await callback_query.message.answer(faq_text)

#     # Сохраняем ID последнего отправленного сообщения
#     await save_last_message(user_id, sent_message)

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