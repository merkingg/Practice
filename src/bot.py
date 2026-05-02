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

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


WAITING_AUTHOR = 1  


GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
BOOKS_PER_PAGE = 3

GENRES = {
    "fiction": ("Художественная литература", "fiction novels"),
    "mystery": ("Детективы и триллеры", "mystery thriller"),
    "fantasy": ("Фэнтези", "fantasy magic"),
    "science fiction": ("Научная фантастика", "science fiction space"),
    "romance": ("Романы", "romance love story"),
    "biography": ("Биографии", "biography memoir"),
    "history": ("История", "history historical"),
    "science": ("Наука", "popular science"),
    "self help": ("Саморазвитие", "self help personal development"),
    "children": ("Детская литература", "children books"),
}

RATINGS = {
    "new":        ("Новинки", None),
    "classic":    ("Классика мировой литературы", "classic literature tolstoy dostoevsky"),
    "bestseller": ("Бестселлеры", None),
    "award":      ("Лауреаты премий", "pulitzer booker prize winner fiction"),
}

NEW_BOOKS = [
    ("Intermezzo", "Sally Rooney"),
    ("The Women", "Kristin Hannah"),
    ("James", "Percival Everett"),
    ("The God of the Woods", "Lauren Fox"),
    ("The Anxious Generation", "Jonathan Haidt"),
    ("Eruption", "Michael Crichton"),
    ("The Life Impossible", "Matt Haig"),
    ("Small Things Like These", "Claire Keegan"),
    ("Orbital", "Samantha Harvey"),
    ("The Frozen River", "Ariel Lawhon"),
    ("Tell Me Everything", "Elizabeth Strout"),
    ("Funny Story", "Emily Henry"),
    ("Onyx Storm", "Rebecca Yarros"),
    ("Wind and Truth", "Brandon Sanderson"),
    ("The Familiar", "Leigh Bardugo"),
    ("The House in the Pines", "Ana Reyes"),
    ("All Fours", "Miranda July"),
    ("Playground", "Richard Powers"),
    ("The Grey Wolf", "Louise Penny"),
    ("Here One Moment", "Liane Moriarty"),
    ("The Wedding People", "Alison Espach"),
    ("North Woods", "Daniel Mason"),
    ("The Sequel", "Jean Hanff Korelitz"),
    ("When the Moon Hatched", "Sarah A. Parker"),
    ("The Forest of Vanishing Stars", "Kristin Hannah"),
]

BESTSELLER_BOOKS = [
    ("Harry Potter and the Sorcerer's Stone", "J.K. Rowling"),
    ("The Da Vinci Code", "Dan Brown"),
    ("The Girl with the Dragon Tattoo", "Stieg Larsson"),
    ("The Hunger Games", "Suzanne Collins"),
    ("Twilight", "Stephenie Meyer"),
    ("Atlas Shrugged", "Ayn Rand"),
    ("A Thousand Splendid Suns", "Khaled Hosseini"),
    ("The Kite Runner", "Khaled Hosseini"),
    ("The Master and Margarita", "Mikhail Bulgakov"),
    ("Crime and Punishment", "Fyodor Dostoevsky"),
    ("War and Peace", "Leo Tolstoy"),
    ("To Kill a Mockingbird", "Harper Lee"),
    ("The Great Gatsby", "F. Scott Fitzgerald"),
    ("1984", "George Orwell"),
    ("Brave New World", "Aldous Huxley"),
    ("Animal Farm", "George Orwell"),
    ("The Little Prince", "Antoine de Saint-Exupery"),
    ("The Catcher in the Rye", "J.D. Salinger"),
    ("The Picture of Dorian Gray", "Oscar Wilde"),
    ("Three Comrades", "Erich Maria Remarque"),
    ("The Call of the Wild", "Jack London"),
    ("Martin Eden", "Jack London"),
    ("The Old Man and the Sea", "Ernest Hemingway"),
    ("Lord of the Flies", "William Golding"),
    ("Little Women", "Louisa May Alcott"),
]


def translate(text: str) -> str:
    if not text:
        return text
    try:
        return GoogleTranslator(source="auto", target="ru").translate(text[:4500])
    except Exception:
        return text


EXCLUDED_WORDS = [
    "encyclopedia", "encyclopaedia", "dictionary", "crossword",
    "reference", "handbook", "энциклопедия", "словарь", "справочник",
    "кроссворд", "учебник", "workbook", "textbook", "almanac"
]

def search_books(query: str, max_results: int = BOOKS_PER_PAGE, book_list: list = None, author_filter: str = None) -> list[dict]:
    import random

    if book_list:
        results = []
        shuffled = random.sample(book_list, len(book_list))
        for title, author in shuffled:
            if len(results) >= max_results:
                break
            params = {
                "q": f"{title} {author}",
                "maxResults": 3,
                "printType": "books",
            }
            api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
            if api_key:
                params["key"] = api_key
            try:
                resp = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
                resp.raise_for_status()
                items = resp.json().get("items", [])
                for item in items:
                    info = item.get("volumeInfo", {})
                    if info.get("authors") and info.get("description"):
                        results.append(item)
                        break
            except Exception as e:
                logger.warning(f"Не удалось найти '{title}': {e}")
        return results

    params = {
        "q": query,
        "maxResults": 15,
        "printType": "books",
        "orderBy": "relevance",
    }
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if api_key:
        params["key"] = api_key

    try:
        resp = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        if resp.status_code == 503:
            simple_query = query.split()[0]
            params["q"] = simple_query
            resp = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)

        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])

        filtered = []
        for item in items:
            info = item.get("volumeInfo", {})
            title = info.get("title", "").lower()
            categories = " ".join(info.get("categories", [])).lower()

            if not info.get("authors") or not info.get("description"):
                continue
            if any(word in title or word in categories for word in EXCLUDED_WORDS):
                continue
            if author_filter:
                book_authors = " ".join(info.get("authors", [])).lower()
                if author_filter.lower() not in book_authors:
                    continue

            filtered.append(item)

        logger.info(f"Запрос: '{query}' → найдено {len(items)}, после фильтрации: {len(filtered)}")
        return filtered[:max_results]

    except Exception as e:
        logger.error(f"Ошибка Google Books API: {e}")
        return []


def format_book(item: dict) -> str:
    info = item.get("volumeInfo", {})
    title = translate(info.get("title", "Без названия"))
    authors = ", ".join(info.get("authors", ["Автор неизвестен"]))
    description = info.get("description", "")
    if description:
        description = translate(description[:500])
    else:
        description = "Описание отсутствует."
    if len(description) > 300:
        description = description[:300].rstrip() + "…"
    rating = info.get("averageRating")
    ratings_count = info.get("ratingsCount", 0)
    year = info.get("publishedDate", "")[:4]
    link = info.get("infoLink", "")

    rating_str = f"⭐ {rating}/5 ({ratings_count} оценок)" if rating else "Нет оценок"
    year_str = f" · {year}" if year else ""

    return (
        f"📖 *{title}*\n"
        f"✍️ {authors}{year_str}\n"
        f"{rating_str}\n"
        f"_{description}_\n"
        f"[Подробнее →]({link})"
    )


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🎭 По жанру", callback_data="menu_genre")],
        [InlineKeyboardButton("✍️ По автору", callback_data="menu_author")],
        [InlineKeyboardButton("⭐ По рейтингу", callback_data="menu_rating")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("◀️ Главное меню", callback_data="menu_main")]]
    )


async def send_books_to_message(message, books: list, title: str) -> None:
    if not books:
        await message.reply_text(
            "😔 К сожалению, книги не найдены. Попробуйте другое имя автора.",
            reply_markup=back_keyboard(),
        )
        return

    await message.reply_text(
        f"📚 *{title}*\nНайдено книг: {len(books)}",
        parse_mode="Markdown",
    )

    for item in books:
        text = format_book(item)
        try:
            await message.reply_text(
                text,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить книгу: {e}")

    await message.reply_text(
        "Выберите следующий поиск:",
        reply_markup=back_keyboard(),
    )


async def send_books(query, books: list, title: str) -> None:
    if not books:
        await query.edit_message_text(
            "😔 К сожалению, книги не найдены. Попробуйте другой запрос.",
            reply_markup=back_keyboard(),
        )
        return

    await query.edit_message_text(
        f"📚 *{title}*\nНайдено книг: {len(books)}",
        parse_mode="Markdown",
    )

    for item in books:
        text = format_book(item)
        try:
            await query.message.reply_text(
                text,
                parse_mode="Markdown",
                disable_web_page_preview=False,
            )
        except Exception as e:
            logger.warning(f"Не удалось отправить книгу: {e}")

    await query.message.reply_text(
        "Выберите следующий поиск:",
        reply_markup=back_keyboard(),
    )


async def ask_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "✍️ Введите имя автора:\n\n"
        "Например: _Стивен Кинг_, _Толстой_, _Stephen King_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("◀️ Отмена", callback_data="menu_main")]]
        ),
    )
    return WAITING_AUTHOR  


async def receive_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    author_name = update.message.text.strip()

    await update.message.reply_text(
        f"🔍 Ищу книги автора «{author_name}»…\n⏳ Перевожу описания, подождите ~30 сек."
    )

    books = search_books(f"inauthor:\"{author_name}\"", author_filter=author_name)
    await send_books_to_message(update.message, books, f"✍️ Автор: {author_name}")

    return ConversationHandler.END


async def cancel_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Выберите критерий поиска:",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_main":
        await query.edit_message_text(
            "Выберите критерий поиска:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu_genre":
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"genre_{key}")]
            for key, (label, _) in GENRES.items()
        ]
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_main")])
        await query.edit_message_text(
            "🎭 Выберите жанр:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if data == "menu_rating":
        keyboard = [
            [InlineKeyboardButton(label, callback_data=f"rating_{key}")]
            for key, (label, _) in RATINGS.items()
        ]
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_main")])
        await query.edit_message_text(
            "⭐ Выберите категорию:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    if data.startswith("genre_"):
        genre_key = data[len("genre_"):]
        genre_label, search_query = GENRES.get(genre_key, (genre_key, genre_key))
        await query.edit_message_text(
            f"🔍 Ищу книги в жанре «{genre_label}»…\n⏳ Перевожу описания, подождите ~30 сек."
        )
        books = search_books(search_query)
        await send_books(query, books, f"🎭 Жанр: {genre_label}")
        return

    if data.startswith("rating_"):
        rating_key = data[len("rating_"):]
        label, search_query = RATINGS.get(rating_key, ("", ""))
        await query.edit_message_text(
            f"🔍 Ищу: «{label}»…\n⏳ Перевожу описания, подождите ~30 сек."
        )
        if rating_key == "bestseller":
            books = search_books("", book_list=BESTSELLER_BOOKS)
        elif rating_key == "new":
            books = search_books("", book_list=NEW_BOOKS)
        else:
            books = search_books(search_query)
        await send_books(query, books, f"⭐ {label}")
        return


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Не задана переменная окружения TELEGRAM_BOT_TOKEN")

    app = Application.builder().token(token).build()

    author_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(ask_author, pattern="^menu_author$")],
        states={
            WAITING_AUTHOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_author)
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_author, pattern="^menu_main$")],
    )

    app.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text(
        "Выберите критерий поиска:",
        reply_markup=main_menu_keyboard(),
    )))
    app.add_handler(author_conv)
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()