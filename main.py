import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# --- 1. ОТРИМАННЯ ДАНИХ З RAILWAY (ENVIRONMENT VARIABLES) ---
TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

# Перевірка наявності даних
if not TOKEN or not DB_URL:
    print("Помилка: BOT_TOKEN або DATABASE_URL не знайдені в змінних оточення!")
    # Для тестів можна тимчасово вписати сюди, якщо Railway не підтягує:
    # TOKEN = "ваш_токен"
    # DB_URL = "ваше_посилання"
    exit(1)

# Автоматичне виправлення протоколу для асинхронності
if "asyncpg" not in DB_URL:
    DB_URL = DB_URL.replace("postgresql://", "postgresql+asyncpg://")

# --- 2. НАЛАШТУВАННЯ БАЗИ ДАНИХ ---
engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 3. ФУНКЦІЯ ПОШУКУ В БД ---
async def get_consumers_from_db(search_query: str):
    async with async_session() as session:
        # ILIKE - пошук без урахування регістру
        sql = text("SELECT id, name, debt_amount, cutoff_date FROM consumers WHERE name ILIKE :q")
        result = await session.execute(sql, {"q": f"%{search_query}%"})
        return result.all()

# --- 4. INLINE ПОШУК ---
@dp.inline_query()
async def search_consumer(inline_query: types.InlineQuery):
    query_text = inline_query.query.strip()
    if not query_text:
        return

    try:
        rows = await get_consumers_from_db(query_text)
        results = []
        for row in rows:
            results.append(
                InlineQueryResultArticle(
                    id=str(row.id),
                    title=row.name,
                    description=f"Борг: {row.debt_amount} грн. Дата: {row.cutoff_date}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"📋 **Інформація з бази:**\n"
                                     f"👤 Споживач: {row.name}\n"
                                     f"💰 Борг: {row.debt_amount} грн\n"
                                     f"📅 Дата відключення: {row.cutoff_date}",
                        parse_mode="Markdown"
                    )
                )
            )
        await inline_query.answer(results, cache_time=1)
    except Exception as e:
        print(f"Помилка бази даних: {e}")

async def main():
    print("Бот запущений і підключений до БД через Railway...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
