from aiogram import Router, types
from aiogram.filters import Command
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
    await send_main_menu(callback_query.bot, user_id, first_name)

async def send_main_menu(bot, user_id, first_name):
    """
    Отправляет главное меню пользователю.
    """
    await delete_previous_message(bot, user_id)

    is_subscribed = await check_subscription(user_id)
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📦 Каталог", callback_data="catalog_page_1")],
        [types.InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
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
