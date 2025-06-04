import logging
from aiogram import Router, types
from sqlalchemy.sql import text
from helpers.database import add_to_cart, async_session_maker
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
        sent_message = await message.answer("❌ Количество должно быть больше 0. Введи снова:")

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
        sent_message = await callback_query.message.answer("❌ Ошибка! Сначала укажи количество товара.")

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

@router.callback_query(lambda callback_query: callback_query.data == "view_cart")
async def view_cart_handler(callback_query: types.CallbackQuery):
    """
    Показывает корзину пользователя в виде карточек товаров.
    """
    user_id = callback_query.from_user.id
    logger.info(f"Получаем `id` для `telegram_id={user_id}`.")

    async with async_session_maker() as session:
        # Получаем `id` по `telegram_id`
        user_check_query = text("SELECT id FROM users_botuser WHERE telegram_id = :user_id")
        result = await session.execute(user_check_query, {"user_id": user_id})
        user_db_id = result.scalar()

        if not user_db_id:
            logger.warning(f"⚠ Ошибка! `telegram_id={user_id}` не найден в `users_botuser`.")
            await callback_query.message.answer("❌ Ошибка! Ваш профиль не найден.")
            return

        await session.commit()
        session.expire_all()

        logger.info(f"`id={user_db_id}` найден! Загружаем корзину...")

        # Запрашиваем товары из `shop_cart` по `id`
        cart_query = text("""
        SELECT shop_product.id, shop_product.name, shop_product.price, shop_product.image, shop_cart.quantity
        FROM shop_cart
        JOIN shop_product ON shop_cart.product_id = shop_product.id
        WHERE shop_cart.user_id = :user_db_id
        """)
        result = await session.execute(cart_query, {"user_db_id": user_db_id})
        cart_items = result.fetchall()

    logger.info(f"Найдено товаров в корзине: {len(cart_items)}")

    if not cart_items:
        logger.warning(f"Корзина пуста для пользователя `id={user_db_id}`!")
        await callback_query.message.answer("🛒 Ваша корзина пуста!")
        return

    # Создаём карточки для каждого товара в корзине
    for item in cart_items:
        product_id, product_name, price, image_url, quantity = item
        logger.info(f"Товар в корзине: {product_name}, Количество: {quantity}")

        cart_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="❌ Удалить", callback_data=f"remove_{product_id}")],
            [types.InlineKeyboardButton(text="✏ Изменить количество", callback_data=f"update_{product_id}")]
        ])

        await callback_query.message.answer_photo(
            photo=image_url,
            caption=f"**{product_name}**\nЦена: {price} ₽\nКоличество: {quantity} шт.",
            reply_markup=cart_keyboard,
            parse_mode="Markdown"
        )

@router.callback_query(lambda callback_query: callback_query.data.startswith("remove_"))
async def remove_from_cart_handler(callback_query: types.CallbackQuery):
    """
    Удаляет товар из корзины и обновляет отображение.
    """
    user_id = callback_query.from_user.id
    product_id = int(callback_query.data.split("_")[-1])

    async with async_session_maker() as session:
        remove_query = text("DELETE FROM shop_cart WHERE user_id = :user_id AND product_id = :product_id")
        await session.execute(remove_query, {"user_id": user_id, "product_id": product_id})
        await session.commit()

    await callback_query.message.answer(f"❌ Товар удалён из корзины!")

    # Обновляем корзину после удаления
    await view_cart_handler(callback_query)

@router.callback_query(lambda callback_query: callback_query.data.startswith("update_"))
async def update_quantity_handler(callback_query: types.CallbackQuery):
    """
    Запрашивает новое количество товара в корзине.
    """
    user_id = callback_query.from_user.id
    product_id = int(callback_query.data.split("_")[-1])

    sent_message = await callback_query.message.answer("✏ Введите новое количество:")
    await save_last_message(user_id, sent_message)

    cart_sessions[user_id] = {"product_id": product_id}

@router.message(lambda message: message.text.isdigit() and message.from_user.id in cart_sessions)
async def confirm_update_handler(message: types.Message):
    """
    Обновляет количество товара в корзине.
    """
    user_id = message.from_user.id
    quantity = int(message.text)

    if quantity <= 0:
        sent_message = await message.answer("❌ Количество должно быть больше 0. Введите снова:")
        await save_last_message(user_id, sent_message)
        return

    product_id = cart_sessions[user_id]["product_id"]

    async with async_session_maker() as session:
        update_query = text("""
        UPDATE shop_cart SET quantity = :quantity WHERE user_id = :user_id AND product_id = :product_id
        """)
        await session.execute(update_query, {"quantity": quantity, "user_id": user_id, "product_id": product_id})
        await session.commit()

    await message.answer(f"✅ Количество товара обновлено: {quantity} шт.")

    # Обновляем корзину после изменения
    await view_cart_handler(types.CallbackQuery(from_user=message.from_user, message=message))
