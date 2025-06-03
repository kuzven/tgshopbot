import logging
from aiogram import Router, types
from helpers.database import get_categories
from settings.config import CATEGORIES_PER_PAGE  # Импортируем число категорий на одной странице

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(lambda callback_query: callback_query.data.startswith("catalog_page_"))
async def catalog_handler(callback_query: types.CallbackQuery):
    """
    Обработчик кнопки "📦 Каталог".
    Загружает категории из БД и показывает их с кнопками.
    """
    user_id = callback_query.from_user.id
    logger.info(f"Обработчик каталога вызван пользователем {user_id}")

    page = int(callback_query.data.split("_")[-1])  # Получаем номер страницы
    logger.info(f"Текущая страница каталога: {page}")

    offset = (page - 1) * CATEGORIES_PER_PAGE
    categories = await get_categories(limit=CATEGORIES_PER_PAGE, offset=offset)
    logger.info(f"Загружено {len(categories)} категорий из БД")
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=category.name, callback_data=f"category_{category.id}")]
        for category in categories
    ])

    # Добавляем кнопки "⬅️ Назад" и "➡️ Вперёд"
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"catalog_page_{page - 1}"))
    if len(categories) == CATEGORIES_PER_PAGE:
        navigation_buttons.append(types.InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"catalog_page_{page + 1}"))

    if navigation_buttons:
        keyboard.inline_keyboard.append(navigation_buttons)

    await callback_query.message.edit_text("Выбери категорию товаров 👇", reply_markup=keyboard)

    logger.info(f"Каталог успешно обновлён для пользователя {user_id}")
