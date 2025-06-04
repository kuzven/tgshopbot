from aiogram import Router, types
from aiogram.filters import Command
from handlers.cart_handler import view_cart_handler
from helpers.database import save_user
from helpers.utils import check_subscription
from helpers.message_manager import delete_previous_message, save_last_message
from settings.config import TG_CHANNEL_URL, TG_GROUP_URL

router = Router()

@router.message(Command("start"))
async def start_message_handler(message: types.Message):
    """
    Обработчик команды /start.
    Отправляет главное меню и сохраняет пользователя.
    """
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # Сохраняем пользователя при первом запуске
    await save_user(message.from_user)

    await send_main_menu(message.bot, user_id, first_name)

@router.callback_query(lambda callback_query: callback_query.data == "start")
async def start_callback_handler(callback_query: types.CallbackQuery):
    """
    Обработчик callback-кнопки "🏠 Главное меню".
    Отправляет главное меню.
    """
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    # Удаляем предыдущее сообщение, если оно есть
    if callback_query.message:
        await delete_previous_message(callback_query.message.bot, user_id)

        # Объявляем переменную sent_message
        sent_message = None

        # Отправляем главное меню
        sent_message = await send_main_menu(callback_query.bot, user_id, first_name)

        # Сохраняем ID последнего отправленного сообщения
        await save_last_message(user_id, sent_message)
    
    else:
        # Если `callback_query.message` нет (из инлайн-режима), просто отправляем главное меню
        await send_main_menu(callback_query.bot, user_id, first_name)

async def send_main_menu(bot, user_id, first_name):
    """
    Отправляет главное меню пользователю.
    """
    await delete_previous_message(bot, user_id)

    is_subscribed = await check_subscription(user_id)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📦 Каталог", callback_data="category_page_1")],
        [types.InlineKeyboardButton(text="🛒 Корзина", callback_data="view_cart")],
        [types.InlineKeyboardButton(text="❓ FAQ", switch_inline_query_current_chat="")]
    ])

    if is_subscribed:
        sent_message = await bot.send_message(
            chat_id=user_id,
            text=f"{first_name}, добро пожаловать в главное меню бота 👋\n\nВыбери раздел 👇",
            reply_markup=keyboard
        )
    else:
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔗 Подписаться на канал", url=TG_CHANNEL_URL)],
            [types.InlineKeyboardButton(text="🔗 Подписаться на группу", url=TG_GROUP_URL)]
        ])
        sent_message = await bot.send_message(chat_id=user_id, text=f"❗ {first_name}, ты не подписан на наш канал и группу!\n\nПодпишись, затем нажми /start", reply_markup=keyboard)

    await save_last_message(user_id, sent_message)

@router.message(Command("cart"))
async def cart_command_handler(message: types.Message):
    """
    Показывает корзину при вводе команды `/cart`.
    """
    user_id = message.from_user.id  # Получаем user_id
    await view_cart_handler(message, user_id)  # Передаём user_id в `view_cart_handler`
