import logging
from aiogram import Router, types
from helpers.database import get_subcategories
from helpers.message_manager import delete_previous_message, save_last_message
from settings.config import SUBCATEGORIES_PER_PAGE

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(lambda callback_query: callback_query.data.startswith("category_") or callback_query.data.startswith("subcategory_page_"))
async def subcategory_handler(callback_query: types.CallbackQuery):
    """
    Обработчик кнопок категорий и пагинации подкатегорий.
    Загружает подкатегории для выбранной категории и переключает страницы.
    """
    user_id = callback_query.from_user.id

    if callback_query.data.startswith("category_"):
        category_id = int(callback_query.data.split("_")[-1])
        page = 1  # Первая страница
    else:
        category_id, page = map(int, callback_query.data.split("_")[2:])  # Страница пагинации

    logger.info(f"Загрузка подкатегорий для категории {category_id}, страница {page}")

    await delete_previous_message(callback_query.message.bot, user_id)

    offset = (page - 1) * SUBCATEGORIES_PER_PAGE
    subcategories = await get_subcategories(category_id, limit=SUBCATEGORIES_PER_PAGE, offset=offset)

    if not subcategories:
        logger.warning(f"❌ В категории {category_id} нет подкатегорий. Показываем кнопку '🏠 Главное меню'.")

        # Удаляем предыдущее сообщение, если оно есть
        await delete_previous_message(callback_query.message.bot, user_id)

        # Объявляем переменную sent_message
        sent_message = None

        # Создаём клавиатуру с кнопкой "🏠 Главное меню"
        main_menu_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
        main_menu_button = types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="start")
        main_menu_keyboard.inline_keyboard.append([main_menu_button])

        logger.info(f"Отправляем кнопку '🏠 Главное меню' пользователю {user_id}")

        sent_message = await callback_query.message.answer("❌ Нет подкатегорий в этой категории.", reply_markup=main_menu_keyboard)

        # Сохраняем ID последнего отправленного сообщения
        await save_last_message(user_id, sent_message)

        return

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=sub.name, callback_data=f"subcategory_{sub.id}")]
        for sub in subcategories
    ])

    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"subcategory_page_{category_id}_{page - 1}"))
    if len(subcategories) == SUBCATEGORIES_PER_PAGE:
        navigation_buttons.append(types.InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"subcategory_page_{category_id}_{page + 1}"))

    if navigation_buttons:
        keyboard.inline_keyboard.append(navigation_buttons)

    sent_message = await callback_query.message.answer(f"Выбери подкатегорию 👇", reply_markup=keyboard)
    await save_last_message(user_id, sent_message)

    logger.info(f"Подкатегории обновлены для пользователя {user_id}")
