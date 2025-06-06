# tgshopbot
Telegram bot shop

## Описание  
Проект **tgshopbot** — это телеграм бот - магазин товаров.

---

## Функции
✅ В каталоге товаров используются категории и подкатегории в формате инлайн кнопок с пагинацией.

✅ Вывод товаров с пагинацией в формате: изображение, название, описание, цена.

✅ Добавление товаров в корзину, изменение количества товаров в корзине и удаление из корзины.

✅ Оформление заказов с указанием данных для доставки.

✅ Оплата заказов через тестовый платёжный шлюз Юкасса.

✅ В разделе FAQ вывод ответов на частозадаваемые вопросы в формате инлайн режима.

✅ Сохранение заказов в Excel файл в папку orders в корне проекта.

✅ Все запросы к базе данных осуществляются асинхронно с помощью SQLAlchemy (Async).

✅ Помещено в Docker-контейнер для удобного развёртывания.

---

## ⚙ Использованные технологии
🔹 Backend: Python 3, Aiogram-3, SQLAlchemy (Async)

🔹 База данных: PostgreSQL

🔹 Платёжный шлюз Юкасса

🔹 Контейнеризация: Docker, Docker Compose

---

## 🛠 Системные требования  
Перед установкой необходимо установить административную панель Django для управления ботом tgshopbot и выполнить все пункты инструкции:  
- **tgshopadmin** → [Инструкция по установке](https://github.com/kuzven/tgshopadmin)  

---

## Инструкция по установке и запуску на сервере с Docker

### **1️⃣ Клонирование репозитория**

```bash
cd ~
git clone https://github.com/kuzven/tgshopbot.git
cd tgshopbot
```

### **2️⃣ Создание .env файла**
- Создаём .env на основе шаблона:

```bash
cp .env.example .env
nano .env
```

- Укажите значения для следующих параметров, например:

```
BOT_TOKEN=your_bot_token
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_RETURN_URL=url_telegram_bot
```

### **3️⃣ Настройка config.py**

```bash
nano settings/config.py
```

- Укажите значения для следующих параметров, например:

```
# Ссылки на канал и группу, на которые нужно подписаться
TG_CHANNEL_URL = "https://t.me/tgshop_channel"
TG_GROUP_URL = "https://t.me/+n-qLN2T8xCZlOTEy"

# ID канала и группы для проверки подписки при старте бота
GROUP_ID = "-4844064739"
CHANNEL_ID = "-1002344931960"

# Настройка каталога категорий
CATEGORIES_PER_PAGE = 3  # Число категорий на одной странице

# Настройка каталога подкатегорий
SUBCATEGORIES_PER_PAGE = 3  # Число подкатегорий на одной странице

# Настройка вывода товаров
PRODUCTS_PER_PAGE = 3  # Количество товаров на одной странице
MEDIA_URL = "http://yourserver.com/media/"  # URL доступа к файлам media из Django для вывода изображений товаров
```

### **4️⃣ Запуск контейнера с weather**
Запускаем контейнеры weather-web и weather-nginx в фоне.

```bash
docker-compose up --build -d
```

### **5️⃣ Проверка запущенных контейнеров**

```bash
docker ps
```

Теперь проект tgshopbot успешно запущен и должен функционировать 🎉