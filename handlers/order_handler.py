from aiogram import Router, types
import logging
from helpers.database import async_session_maker
from helpers.message_manager import delete_previous_message, delete_all_previous_messages
from sqlalchemy.sql import text

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
    Создаёт заказ и подтверждает его пользователю.
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

        # ✅ Добавляем товары в заказ
        cart_query = text("SELECT product_id, quantity FROM shop_cart WHERE user_id = :user_db_id")
        result = await session.execute(cart_query, {"user_db_id": user_db_id})
        cart_items = result.fetchall()

        for product_id, quantity in cart_items:
            add_order_item_query = text("""
            INSERT INTO shop_orderitem (order_id, product_id, quantity)
            VALUES (:order_id, :product_id, :quantity)
            """)
            await session.execute(add_order_item_query, {"order_id": order_id, "product_id": product_id, "quantity": quantity})

        await session.commit()
        logger.info(f"Все товары из корзины добавлены в заказ `{order_id}`.")

        # Очищаем корзину пользователя
        await session.execute(text("DELETE FROM shop_cart WHERE user_id = :user_db_id"), {"user_db_id": user_db_id})
        await session.commit()
        logger.info(f"Корзина пользователя `{user_id}` успешно очищена!")

    # Удаляем предыдущее сообщение с запросом доставки
    await delete_previous_message(message.bot, user_id)
    logger.info(f"Сообщение запроса доставки пользователя `{user_id}` удалено.")

    # Клавиатура с кнопкой "🏠 Главное меню"
    menu_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")]
    ])

    # Подтверждение заказа
    sent_message = await message.answer("✅ Заказ принят, ожидай доставку!", reply_markup=menu_keyboard)
    logger.info(f"Сохранён ID сообщения `{sent_message.message_id}` для подтверждения заказа пользователя `{user_id}`.")

    # Удаляем данные из `order_sessions`
    del order_sessions[user_id]
    logger.info(f"`order_sessions[{user_id}]` Данные `order_sessions` удалены успешно!")
