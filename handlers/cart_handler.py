import logging
from aiogram import Router, types
from helpers.database import add_to_cart
from helpers.message_manager import delete_previous_message, save_last_message, delete_all_previous_messages

logger = logging.getLogger(__name__)
router = Router()

# Создаём хранилище ID последних 3 сообщений с товарами
user_messages = {}

# Объявляем `cart_sessions` как глобальную переменную
cart_sessions = {}

@router.callback_query(lambda callback_query: callback_query.data.startswith("add_to_cart_"))
async def ask_quantity_handler(callback_query: types.CallbackQuery):
    """
    Запрашивает у пользователя количество товара перед добавлением в корзину.
    """
    user_id = callback_query.from_user.id
    product_id = int(callback_query.data.split("_")[-1])
    product_name = callback_query.message.caption.split("\n")[0]

    logger.info(f"🛒 Пользователь {user_id} выбрал товар {product_id}, запрашиваем количество.")

    # Удаляем ВСЕ предыдущие сообщения с товарами
    await delete_all_previous_messages(callback_query.message.bot, user_id)

    # Объявляем переменную sent_message
    sent_message = None  

    sent_message = await callback_query.message.answer("Отправьте цифрами количество товаров:")
    
    # Сохраняем ID последнего отправленного сообщения
    await save_last_message(user_id, sent_message)

    # Сохраняем product_id во временное хранилище
    cart_sessions[user_id] = {"product_id": product_id, "product_name": product_name}

@router.message(lambda message: message.text.isdigit() and message.from_user.id in cart_sessions)
async def confirm_cart_handler(message: types.Message):
    """
    Подтверждает добавление товара в корзину.
    """
    user_id = message.from_user.id
    quantity = int(message.text)

    # Удаляем предыдущее сообщение, если оно есть
    await delete_previous_message(message.bot, user_id)

    # Объявляем переменную sent_message
    sent_message = None  

    if quantity <= 0:
        sent_message = await message.answer("❌ Количество должно быть больше 0. Введите снова:")

        # Сохраняем ID последнего отправленного сообщения
        await save_last_message(user_id, sent_message)

        return

    product_name = cart_sessions[user_id]["product_name"]
    cart_sessions[user_id]["quantity"] = quantity

    confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_cart")],
        [types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")]
    ])

    sent_message = await message.answer(f"Ты действительно хочешь добавить в корзину {quantity} шт. товара {product_name}?", reply_markup=confirm_keyboard)

    # Сохраняем ID последнего отправленного сообщения
    await save_last_message(user_id, sent_message)


@router.callback_query(lambda callback_query: callback_query.data == "confirm_cart")
async def add_cart_handler(callback_query: types.CallbackQuery):
    """
    Добавляет товар в корзину после подтверждения.
    """
    user_id = callback_query.from_user.id

    # Удаляем предыдущее сообщение, если оно есть
    await delete_previous_message(callback_query.message.bot, user_id)

    # Объявляем переменную sent_message
    sent_message = None  

    if user_id not in cart_sessions:
        sent_message = await callback_query.message.answer("❌ Ошибка! Сначала укажите количество товара.")

        # Сохраняем ID последнего отправленного сообщения
        await save_last_message(user_id, sent_message)

        return

    product_id = cart_sessions[user_id]["product_id"]
    product_name = cart_sessions[user_id]["product_name"]
    quantity = cart_sessions[user_id]["quantity"]

    await add_to_cart(user_id, product_id, quantity)

    # Создаём клавиатуру с кнопками
    cart_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data="view_cart")],
        [types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")]
    ])

    sent_message = await callback_query.message.answer(
        f"✅ {quantity} шт. товара {product_name} добавлены в корзину!", reply_markup=cart_keyboard
    )

    # Сохраняем ID последнего отправленного сообщения
    await save_last_message(user_id, sent_message)

    # Удаляем сессию после добавления
    del cart_sessions[user_id]
