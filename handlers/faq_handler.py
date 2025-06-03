import logging
from aiogram import Router, types
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
    user_query = query.query.lower()
    questions = await get_questions()

    # Фильтруем вопросы по пользовательскому запросу
    results = [
        types.InlineQueryResultArticle(
            id=str(q.id),
            title=q.text,
            input_message_content=types.InputTextMessageContent(message_text=f"❓ *{q.text}*\n\n{q.answer}"),
            description=q.answer[:50]  # Показываем превью ответа
        )
        for q in questions if user_query in q.text.lower()
    ]

    await query.answer(results, cache_time=1)
