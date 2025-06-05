import os
import logging
import uuid
from aiogram import Router, types
from yookassa import Configuration, Payment
from helpers.database import async_session_maker
from helpers.message_manager import delete_previous_message
from sqlalchemy.sql import text
from dotenv import load_dotenv

# Загружаем `.env`
load_dotenv()

# Подключаем Юкассу
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")
YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL")

# Настраиваем авторизацию Юкасса
Configuration.account_id = YOOKASSA_SHOP_ID
Configuration.secret_key = YOOKASSA_SECRET_KEY

router = Router()
logger = logging.getLogger(__name__)

# Сохраняем данные о текущем заказе пользователя
order_sessions = {}

@router.callback_query(lambda callback_query: callback_query.data == "checkout")
async def ask_delivery_info_handler(callback_query: types.CallbackQuery):
    """
    Запрашивает у пользователя данные для доставки заказа.
    """
    user_id = callback_query.from_user.id
    logger.info(f"Пользователь `{user_id}` начал оформление заказа!")

    # Удаляем предыдущее сообщение перед запросом доставки
    await delete_previous_message(callback_query.message.bot, user_id)

    sent_message = await callback_query.message.answer("Введи данные для доставки (адрес, телефон и др.) 👇")

    # Запоминаем сообщение с запросом доставки для последующего удаления
    order_sessions[user_id] = {"message_id": sent_message.message_id}
    logger.info(f"Сохранён ID сообщения `{sent_message.message_id}` для запроса данных доставки пользователя `{user_id}`.")

@router.message(lambda message: message.from_user.id in order_sessions)
async def confirm_order_handler(message: types.Message):
    """
    Создаёт заказ и отправляет ссылку для оплаты в Юкасса.
    """
    user_id = message.from_user.id
    delivery_info = message.text
    logger.info(f"Получены данные доставки от `{user_id}`: {delivery_info}")

    async with async_session_maker() as session:
        # Получаем `id` пользователя
        user_query = text("SELECT id FROM users_botuser WHERE telegram_id = :user_id")
        result = await session.execute(user_query, {"user_id": user_id})
        user_db_id = result.scalar()

        if not user_db_id:
            logger.warning(f"❌ Ошибка! `telegram_id={user_id}` не найден в `users_botuser`.")
            await message.answer("❌ Ошибка! Ваш профиль не найден.")
            return

        # Создаём новый заказ
        create_order_query = text("""
        INSERT INTO shop_order (user_id, created_at, delivery_info)
        VALUES (:user_db_id, NOW(), :delivery_info)
        RETURNING id
        """)
        result = await session.execute(create_order_query, {"user_db_id": user_db_id, "delivery_info": delivery_info})
        order_id = result.scalar()
        await session.commit()

        logger.info(f"✅ Заказ `{order_id}` успешно создан для пользователя `{user_id}`.")

        # Добавляем товары в заказ
        cart_query = text("SELECT product_id, quantity FROM shop_cart WHERE user_id = :user_db_id")
        result = await session.execute(cart_query, {"user_db_id": user_db_id})
        cart_items = result.fetchall()

        total_amount = 0.0
        for product_id, quantity in cart_items:
            product_query = text("SELECT price FROM shop_product WHERE id = :product_id")
            result = await session.execute(product_query, {"product_id": product_id})
            product_price = result.scalar()

            add_order_item_query = text("""
            INSERT INTO shop_orderitem (order_id, product_id, quantity)
            VALUES (:order_id, :product_id, :quantity)
            """)
            await session.execute(add_order_item_query, {"order_id": order_id, "product_id": product_id, "quantity": quantity})
            
            total_amount += float(product_price) * quantity

        await session.commit()
        logger.info(f"Все товары из корзины добавлены в заказ `{order_id}`.")

        # Очищаем корзину пользователя
        await session.execute(text("DELETE FROM shop_cart WHERE user_id = :user_db_id"), {"user_db_id": user_db_id})
        await session.commit()
        logger.info(f"Корзина пользователя `{user_id}` успешно очищена!")

    # Удаляем предыдущее сообщение с запросом доставки
    await delete_previous_message(message.bot, user_id)
    logger.info(f"Сообщение запроса доставки пользователя `{user_id}` удалено.")

    # Генерируем уникальный `idempotence_key` для Юкасса
    idempotence_key = str(uuid.uuid4())

    # Создаём платёж через Юкасса
    payment = Payment.create({
        "amount": {"value": f"{total_amount:.2f}", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": YOOKASSA_RETURN_URL},
        "capture": True,
        "description": f"Оплата заказа №{order_id}"
    }, idempotence_key)  # Передаём `idempotence_key`

    payment_url = payment.confirmation.confirmation_url
    logger.info(f"Сгенерирована ссылка для оплаты заказа `{order_id}`: {payment_url}")

    # Клавиатура с кнопкой "🏠 Главное меню"
    menu_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💳 Оплатить заказ", url=payment_url)],
        [types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")]
    ])

    # Подтверждение заказа
    sent_message = await message.answer("✅ Заказ принят, произведи оплату!", reply_markup=menu_keyboard)
    logger.info(f"Сохранён ID сообщения `{sent_message.message_id}` для подтверждения заказа пользователя `{user_id}`.")

    # Удаляем данные из `order_sessions`
    del order_sessions[user_id]
    logger.info(f"`order_sessions[{user_id}]` Данные `order_sessions` удалены успешно!")
