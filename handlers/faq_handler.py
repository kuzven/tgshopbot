import logging
from aiogram import Router, types
from aiogram.filters import Command
from helpers.database import get_questions
from helpers.message_manager import delete_previous_message, save_last_message

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(lambda callback_query: callback_query.data == "faq")
async def faq_handler(callback_query: types.CallbackQuery):
    """
    Обработчик кнопки FAQ.
    Загружает вопросы из БД и показывает их пользователю.
    """
    user_id = callback_query.from_user.id
    logger.info(f"Обработчик FAQ вызван пользователем {user_id}")

    # Удаляем предыдущее сообщение, если оно есть
    await delete_previous_message(callback_query.message.bot, user_id)

    # Объявляем переменную sent_message
    sent_message = None  

    questions = await get_questions()
    logger.info(f"Загружено {len(questions)} вопросов из БД")

    if not questions:
        logger.warning("База данных пустая! Отправляем сообщение о пустом FAQ.")
        sent_message = await callback_query.message.answer("❗ В базе данных пока нет вопросов и ответов!")
    else:
        faq_text = "❓ **Часто задаваемые вопросы**:\n\n" + "\n\n".join(
            [f"📌 {q.text}" for q in questions]
        )
        sent_message = await callback_query.message.answer(faq_text)

    # Сохраняем ID последнего отправленного сообщения
    await save_last_message(user_id, sent_message)

    logger.info(f"Отправлено сообщение с FAQ пользователю {user_id}")

@router.inline_query()
async def faq_inline_query(query: types.InlineQuery):
    """
    Обработчик инлайн-запросов для FAQ.
    Автоматически дополняет вопросы и показывает ответы.
    """
    user_id = query.from_user.id
    logger.info(f"Получен инлайн-запрос: {query.query} от {query.from_user.id}")

    # Удаляем предыдущее сообщение, если оно есть
    await delete_previous_message(query.bot, user_id)

    user_query = query.query.lower().strip()  # Убираем пробелы и приводим к нижнему регистру
    questions = await get_questions()
    logger.info(f"Всего загружено {len(questions)} вопросов из БД")

    # Фильтруем вопросы по пользовательскому запросу
    results = [
        types.InlineQueryResultArticle(
            id=str(q.id),
            title=q.text,
            # input_message_content=types.InputTextMessageContent(message_text=f"❓ *{q.text}*\n\n{q.answer}"),
            input_message_content=types.InputTextMessageContent(
                message_text=f"❓ *{q.text}*\n\n{q.answer}",
                parse_mode="Markdown"
            ),
            description=q.answer[:50],  # Показываем превью ответа
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔍 Другой вопрос", switch_inline_query_current_chat="")],
                [types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")]
            ])
        )
        for q in questions if user_query in q.text.lower() or q.text.lower().startswith(user_query)
    ]

    await query.answer(results, cache_time=0)

    logger.info(f"Инлайн-ответ отправлен пользователю {user_id}")

@router.message(Command("faq"))
async def faq_command_handler(message: types.Message):
    """
    Обработчик команды /faq.
    Запускает инлайн-режим FAQ так же, как кнопка "❓ FAQ".
    """
    user_id = message.from_user.id

    # Удаляем предыдущее сообщение, если оно есть
    await delete_previous_message(message.bot, user_id)

    # Объявляем переменную sent_message
    sent_message = None  

    bot_username = (await message.bot.get_me()).username  # Получаем имя бота
    switch_inline_query = f"@{bot_username} "  # Подставляем инлайн-запрос в поле ввода

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔍 Открыть FAQ", switch_inline_query_current_chat="")]
    ])

    sent_message = await message.answer(
        f"🔍 Введите ваш вопрос после @{bot_username}, чтобы получить ответ из FAQ.",
        reply_markup=keyboard
    )

    # Сохраняем ID последнего отправленного сообщения
    await save_last_message(user_id, sent_message)
