# Техническое руководство: Telegram-бот для поиска книг «ПолиКот советует»

## Стек технологий

| Технология | Версия | Назначение |
|---|---|---|
| Python | 3.13 | Язык программирования |
| python-telegram-bot | 21.5 | Работа с Telegram Bot API |
| requests | 2.32.3 | HTTP-запросы к Google Books API |
| deep-translator | latest | Автоперевод описаний на русский язык |
| Google Books API | v1 | База данных книг |
| Railway | — | Облачный хостинг для бота |

---

## 1. Исследование предметной области

### 1.1 Постановка задачи

Цель проекта — создать Telegram-бота, который помогает пользователям находить книги по трём критериям: жанру, автору и рейтингу. Бот должен работать на русском языке и предоставлять актуальные данные.

### 1.2 Анализ источников данных

В ходе исследования были рассмотрены следующие API:

| API | Плюсы | Минусы | Итог |
|---|---|---|---|
| Google Books API | Бесплатно, актуально, без регистрации | Лимит 1000 запросов/день, описания на английском | ✅ Выбрано |
| Open Library API | Открытые данные, нет лимитов | Мало метаданных, медленный | ❌ |
| ЛитРес API | Русскоязычный | Только для партнёров | ❌ |
| Goodreads API | Богатые данные | Закрыт для новых разработчиков | ❌ |

### 1.3 Анализ Telegram Bot API

Telegram предоставляет два типа интерфейса для ботов:

| Тип | Описание | Применение в проекте |
|---|---|---|
| ReplyKeyboard | Кнопки внизу экрана | Не используется |
| InlineKeyboard | Кнопки прямо в сообщении | ✅ Используется |
| ConversationHandler | Диалог с ожиданием ввода | ✅ Используется для поиска по автору |

### 1.4 Последовательность исследования

```
Шаг 1: Определение целевой аудитории
        (читатели, студенты, любители книг)
              ↓
Шаг 2: Анализ существующих книжных ботов
        (изучение аналогов в Telegram)
              ↓
Шаг 3: Выбор источника данных
        (сравнение API, выбор Google Books)
              ↓
Шаг 4: Проектирование UX (сценарии использования)
        (главное меню → подкатегории → результаты)
              ↓
Шаг 5: Выбор технологического стека
        (Python + python-telegram-bot)
              ↓
Шаг 6: Разработка и тестирование
        (написание кода, отладка)
              ↓
Шаг 7: Модификация и улучшения
        (перевод, фильтрация, свободный ввод автора)
              ↓
Шаг 8: Развёртывание
        (Railway — облачный сервер)
```

---

## 2. Архитектура проекта

### 2.1 Общая схема работы

```
Пользователь (Telegram)
        │
        │  нажимает кнопку / вводит текст
        ▼
Telegram Bot API
(серверы Telegram)
        │
        │  передаёт событие боту
        ▼
bot.py (Python, Railway)
        │
        ├──► Google Books API
        │    (поиск книг по запросу)
        │           │
        │           ▼
        │    Список книг в формате JSON
        │           │
        ├──► Google Translate (deep-translator)
        │    (перевод названий и описаний)
        │           │
        ▼           ▼
    Форматирование ответа
        │
        ▼
Отправка сообщений пользователю
```

### 2.2 UML-диаграмма вариантов использования

```
                    ┌─────────────────────────────┐
                    │        Telegram-бот         │
                    │                             │
  ┌──────────┐      │  ┌──────────────────────┐   │
  │          │─────►│  │  Поиск по жанру      │   │
  │          │      │  └──────────────────────┘   │
  │Пользо-   │      │  ┌──────────────────────┐   │
  │ватель    │─────►│  │  Поиск по автору     │   │
  │          │      │  └──────────────────────┘   │
  │          │      │  ┌──────────────────────┐   │
  │          │─────►│  │  Поиск по рейтингу   │   │
  └──────────┘      │  └──────────────────────┘   │
                    └─────────────────────────────┘
```

### 2.3 Схема навигации (UX Flow)

```
/start
  └──  Главное меню
        │
        ├── По жанру
        │     ├── Художественная литература ──►  3 книги
        │     ├── Детективы и триллеры      ──►  3 книги
        │     ├── Фэнтези                   ──►  3 книги
        │     ├── Научная фантастика        ──►  3 книги
        │     ├── Романы                    ──►  3 книги
        │     ├── Биографии                 ──►  3 книги
        │     ├── История                   ──►  3 книги
        │     ├── Наука                     ──►  3 книги
        │     ├── Саморазвитие              ──►  3 книги
        │     └── Детская литература        ──►  3 книги
        │
        ├── По автору
        │     └── [пользователь вводит имя] ──►  3 книги
        │
        └── По рейтингу
              ├── Новинки          ──►  3 книги (из списка 25)
              ├── Классика         ──►  3 книги
              ├── Бестселлеры      ──►  3 книги (из списка 25)
              └── Лауреаты премий  ──►  3 книги
```

### 2.4 Структура файлов

```
Practice/
└─ Procfile            	    ← инструкция запуска для Railway
└──src/
    ├── bot.py              ← основная логика (все функции бота)
    ├── requirements.txt    ← список зависимостей Python
    ├── technical manual    ← техническое руководство
    └── final report        ← финальный отчет


```

---

## 3. Пошаговое руководство по созданию бота

### Шаг 1 — Создание бота в BotFather

1. Откройте Telegram → найдите **@BotFather**
2. Отправьте `/newbot`
3. Введите имя: `ПолиКот советует`
4. Введите username: `PolykotBookBot`
5. Скопируйте токен:

```
Token: 123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
### Шаг 2 — Установка зависимостей

```bash
py -m pip install python-telegram-bot==21.5
py -m pip install requests==2.32.3
py -m pip install deep-translator
```

Файл `requirements.txt`:

```
python-telegram-bot==21.5
requests==2.32.3
deep-translator
```

---

### Шаг 3 — Структура кода

#### 3.1 Импорты

```python
import logging
import os
import requests
from deep_translator import GoogleTranslator
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
```

#### 3.2 Словари с данными

```python
# Жанры: ключ → (русское название, поисковый запрос для API)
GENRES = {
    "fiction": ("Художественная литература", "fiction novels"),
    "mystery": ("Детективы и триллеры", "mystery thriller"),
    "fantasy": ("Фэнтези", "fantasy magic"),
    # ...
}

# Категории рейтинга: ключ → (русское название, поисковый запрос)
RATINGS = {
    "new":        ("Новинки", None),           # None = используем список NEW_BOOKS
    "classic":    ("Классика", "classic literature"),
    "bestseller": ("Бестселлеры", None),       # None = используем список BESTSELLER_BOOKS
    "award":      ("Лауреаты премий", "pulitzer booker prize winner fiction"),
}
```

#### 3.3 Функция поиска книг

```python
def search_books(query: str, max_results: int = 3,
                 book_list: list = None,
                 author_filter: str = None) -> list[dict]:

    # Если передан готовый список — ищем каждую книгу отдельно
    if book_list:
        import random
        results = []
        shuffled = random.sample(book_list, len(book_list))
        for title, author in shuffled:
            if len(results) >= max_results:
                break
            params = {"q": f"{title} {author}", "maxResults": 3, "printType": "books"}
            resp = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
            items = resp.json().get("items", [])
            for item in items:
                info = item.get("volumeInfo", {})
                if info.get("authors") and info.get("description"):
                    results.append(item)
                    break
        return results

    # Обычный поиск по запросу
    params = {"q": query, "maxResults": 15, "printType": "books", "orderBy": "relevance"}
    resp = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
    items = resp.json().get("items", [])

    # Фильтрация результатов
    filtered = []
    for item in items:
        info = item.get("volumeInfo", {})
        if not info.get("authors") or not info.get("description"):
            continue  # пропускаем книги без автора или описания
        if author_filter:
            book_authors = " ".join(info.get("authors", [])).lower()
            if author_filter.lower() not in book_authors:
                continue  # пропускаем если автор не совпадает
        filtered.append(item)

    return filtered[:max_results]
```

#### 3.4 Кнопки (InlineKeyboard)

```python
def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎭 По жанру",   callback_data="menu_genre")],
        [InlineKeyboardButton("✍️ По автору",  callback_data="menu_author")],
        [InlineKeyboardButton("⭐ По рейтингу", callback_data="menu_rating")],
    ]
    return InlineKeyboardMarkup(keyboard)
```

#### 3.5 Диалог ввода автора (ConversationHandler)

```python
# Состояние диалога
WAITING_AUTHOR = 1

async def ask_author(update, context) -> int:
    """Шаг 1: просим ввести имя автора"""
    await update.callback_query.edit_message_text(
        "✍️ Введите имя автора:\nНапример: Стивен Кинг, Толстой"
    )
    return WAITING_AUTHOR  # переходим в режим ожидания

async def receive_author(update, context) -> int:
    """Шаг 2: получаем имя и ищем книги"""
    author_name = update.message.text.strip()
    books = search_books(
        f'inauthor:"{author_name}"',
        author_filter=author_name
    )
    await send_books_to_message(update.message, books, f"✍️ Автор: {author_name}")
    return ConversationHandler.END  # завершаем диалог
```

#### 3.6 Точка входа

```python
def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()

    # Обработчик диалога с автором
    author_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_author, pattern="^menu_author$")],
        states={WAITING_AUTHOR: [MessageHandler(filters.TEXT, receive_author)]},
        fallbacks=[CallbackQueryHandler(cancel_author, pattern="^menu_main$")],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(author_conv)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
```

---

### Шаг 4 — Запуск бота

```powershell
# Windows PowerShell
$env:TELEGRAM_BOT_TOKEN="ваш_токен"
$env:GOOGLE_BOOKS_API_KEY="ваш_ключ_api"
py bot.py
```

```bash
# macOS / Linux
export TELEGRAM_BOT_TOKEN="ваш_токен"
export GOOGLE_BOOKS_API_KEY="ваш_ключ_api"
python bot.py
```

---

## 4. UML-диаграммы

### 4.1 Диаграмма последовательности — поиск по жанру

```
Пользователь    Telegram API      bot.py       Google Books API
     │               │               │                │
     │──/start──────►│               │                │
     │               │──событие─────►│                │
     │               │◄──меню────────│                │
     │◄──меню────────│               │                │
     │               │               │                │
     │──По жанру────►│               │                │
     │               │──callback────►│                │
     │               │◄──жанры───────│                │
     │◄──жанры───────│               │                │
     │               │               │                │
     │──Фэнтези─────►│               │                │
     │               │──callback────►│                │
     │               │               │──запрос───────►│
     │               │               │◄──книги────────│
     │               │               │──перевод──     │
     │               │◄──книги───────│                │
     │◄──книги───────│               │                │
```

### 4.2 Диаграмма последовательности — поиск по автору

```
Пользователь    Telegram API      bot.py       Google Books API
     │               │               │                │
     │──По автору───►│               │                │
     │               │──callback────►│                │
     │               │◄──"введите"───│                │
     │◄──"введите"───│               │                │
     │               │               │                │
     │──"Кинг"──────►│               │                │
     │               │──текст───────►│                │
     │               │               │──inauthor:────►│
     │               │               │◄──книги────────│
     │               │               │──фильтрация    │
     │               │               │──перевод       │
     │               │◄──книги───────│                │
     │◄──книги───────│               │                │
```

### 4.3 Диаграмма состояний бота

```
         ┌─────────────────┐
    ─────► Ожидание /start │
         └────────┬────────┘
                  │ /start
                  ▼
         ┌─────────────────┐
         │  Главное меню   │◄─────────────────┐
         └────────┬────────┘                  │
                  │                           │
       ┌──────────┼──────────┐                │
       │          │          │                │
       ▼          ▼          ▼                │
  ┌────────┐ ┌────────┐ ┌────────┐            │
  │ Жанры  │ │ Автор  │ │ Рейтинг│            │
  └───┬────┘ └───┬────┘ └───┬────┘            │
      │          │          │                 │
      │    ┌─────┘          │                 │
      │    ▼                │                 │
      │ ┌──────────────┐    │                 │
      │ │ Ожидание     │    │                 │
      │ │ ввода имени  │    │                 │
      │ └──────┬───────┘    │                 │
      │        │            │                 │
      └────────┼────────────┘                 │
               ▼                              │
         ┌─────────────────┐                  │
         │  Результаты     │──────────────────┘
         │  (3 книги)      │  нажатие "Главное меню"
         └─────────────────┘
```

### 4.4 Диаграмма компонентов

```
┌─────────────────────────────────────────────┐
│                   bot.py                    │
│                                             │
│  ┌────────────┐    ┌──────────────────────┐ │
│  │  Handlers  │    │     Data Layer       │ │
│  │            │    │                      │ │
│  │ button_    │    │ GENRES {}            │ │
│  │ handler()  │    │ RATINGS {}           │ │
│  │            │    │ NEW_BOOKS []         │ │
│  │ ask_author │    │ BESTSELLER_BOOKS []  │ │
│  │ ()         │    │ EXCLUDED_WORDS []    │ │
│  │            │    └──────────────────────┘ │
│  │ receive_   │                             │
│  │ author()   │    ┌──────────────────────┐ │
│  └────────────┘    │    API Layer         │ │
│                    │                      │ │
│  ┌────────────┐    │ search_books()       │ │
│  │    UI      │    │ translate()          │ │
│  │            │    │ format_book()        │ │
│  │ main_menu_ │    └──────────────────────┘ │
│  │ keyboard() │                             │
│  │ back_      │                             │
│  │ keyboard() │                             │
│  └────────────┘                             │
└──────────────────┬──────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌─────────────────┐
│ Telegram API  │    │ Google Books API│
│ (серверы TG)  │    │ + Translate     │
└───────────────┘    └─────────────────┘
```

---

## 5. Модификации проекта

В ходе разработки были реализованы следующие модификации:

### 5.1 Свободный ввод имени автора

**До модификации:** пользователь выбирал автора из фиксированного списка 10 авторов.

**После модификации:** пользователь вводит любое имя текстом — бот ищет книги этого автора в реальном времени через Google Books API.

**Реализация:** использован `ConversationHandler` — механизм python-telegram-bot для ведения многошагового диалога.

```python
# До: фиксированный список
AUTHORS = {
    "Stephen King": "Стивен Кинг",
    "Agatha Christie": "Агата Кристи",
    # ...только 10 авторов
}

# После: свободный ввод + поиск по API
async def receive_author(update, context) -> int:
    author_name = update.message.text.strip()
    books = search_books(f'inauthor:"{author_name}"', author_filter=author_name)
    # ...отправляем результаты
```

### 5.2 Автоперевод на русский язык

**До модификации:** описания книг отображались на английском языке.

**После модификации:** названия и описания автоматически переводятся на русский через `deep-translator`.

```python
from deep_translator import GoogleTranslator

def translate(text: str) -> str:
    return GoogleTranslator(source="auto", target="ru").translate(text[:4500])
```

### 5.3 Фиксированные списки для новинок и бестселлеров

**До модификации:** поиск новинок и бестселлеров через Google Books API давал нерелевантные результаты (путеводители, учебники, старые книги).

**После модификации:** созданы два кураторских списка по 25 книг каждый. Бот случайно выбирает 3 книги из списка и находит их в Google Books API.

```python
NEW_BOOKS = [
    ("Intermezzo", "Sally Rooney"),
    ("The Women", "Kristin Hannah"),
    # ...25 книг
]

BESTSELLER_BOOKS = [
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling"),
    ("The Da Vinci Code", "Dan Brown"),
    # ...25 книг
]
```

### 5.4 Фильтрация нежелательных книг

**До модификации:** в результатах появлялись энциклопедии, кроссворды, справочники.

**После модификации:** добавлен список стоп-слов — книги с такими словами в названии или категории исключаются из выдачи.

```python
EXCLUDED_WORDS = [
    "encyclopedia", "dictionary", "crossword", "handbook",
    "энциклопедия", "словарь", "справочник", "кроссворд",
    "workbook", "textbook", "almanac"
]
```

### 5.5 Улучшенная навигация

**До модификации:** кнопка «Главное меню» была прикреплена к последней книге — при нажатии книга исчезала.

**После модификации:** кнопка «Главное меню» отправляется отдельным сообщением после всех книг — ни одна книга не пропадает.

---

## 6. Развёртывание на Railway

### 6.1 Схема развёртывания

```
Локальная машина          GitHub             Railway (сервер)
      │                     │                      │
      │──push bot.py───────►│                      │
      │──push requirements─►│                      │
      │──push Procfile─────►│                      │
      │                     │                      │
      │                     │──автодеплой─────────►│
      │                     │                      │──pip install
      │                     │                      │──py bot.py
      │                     │                      │
      │                     │                 Бот работает бесперебойно
```

### 6.2 Файл Procfile

```
worker: python bot.py
```

### 6.3 Переменные окружения на Railway

| Переменная | Значение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен от BotFather |
| `GOOGLE_BOOKS_API_KEY` | ключ от Google Cloud Console |

---

## 7. Лимиты и ограничения

| Ограничение | Значение | Решение |
|---|---|---|
| Google Books API без ключа | 1 000 запросов/день | Получить API-ключ |
| Google Books API с ключом | 1 000 запросов/день | Кэширование результатов |
| Ошибка 503 | Временная недоступность API | Повторный запрос с упрощённым запросом |
| Ошибка 429 | Превышен дневной лимит | Ждать до следующего дня |
| Перевод | ~2 сек на книгу | Предупреждение пользователя |
