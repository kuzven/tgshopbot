from aiogram import Router, types
from aiogram.filters import Command
from helpers.utils import check_subscription
from helpers.message_manager import delete_previous_message, save_last_message

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    """
    Обработчик команды /start.
    Проверяет подписку пользователя и отправляет приветственное сообщение.
    """
    user_id = message.from_user.id

    # Удаляем предыдущее сообщение, если оно есть
    await delete_previous_message(message.bot, user_id)

    is_subscribed = await check_subscription(user_id)
    
    # Объявляем переменную sent_message
    sent_message = None  

    if is_subscribed:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📦 Каталог", callback_data="catalog_page_1")],
            [types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [types.InlineKeyboardButton(text="❓ FAQ", switch_inline_query_current_chat="")]
        ])
        sent_message = await message.answer("Добро пожаловать в бот 👋, выбери раздел 👇", reply_markup=keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔗 Подписаться на канал", url="https://t.me/tgshop_channel")],
            [types.InlineKeyboardButton(text="🔗 Подписаться на группу", url="https://t.me/+n-qLN2T8xCZlOTEy")]
        ])
        sent_message = await message.answer("❗ Ты не подписан на наш канал и группу! Для использования бота подпишись по кнопкам ниже, затем нажми /start чтобы проверить подписку!", reply_markup=keyboard)

    # Сохраняем ID последнего отправленного сообщения
    await save_last_message(user_id, sent_message)