import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# --- 1. ЗАВАНТАЖЕННЯ КОНФІГУРАЦІЇ З VARIABLES ---
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

# Перевірка наявності змінних
if not TOKEN or not DB_URL:
    print("❌ ПОМИЛКА: Перевірте файл .env або системні змінні (Variables)!")
    exit(1)

# --- 2. НАЛАШТУВАННЯ БАЗИ ДАНИХ ---
engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 3. ФУНКЦІЯ ПОШУКУ В БД ---
async def get_consumers_from_db(search_query: str):
    async with async_session() as session:
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
                    id=str(row[0]), # row.id
                    title=row[1], # row.name
                    description=f"Борг: {row[2]} грн. Дата: {row[3]}",
                    input_message_content=InputTextMessageContent(
                        message_text=f"📋 **Інформація з бази:**\n"
                                     f"👤 Споживач: {row[1]}\n"
                                     f"💰 Борг: {row[2]} грн\n"
                                     f"📅 Дата відключення: {row[3]}",
                        parse_mode="Markdown"
                    )
                )
            )
        await inline_query.answer(results, cache_time=1)
    except Exception as e:
        print(f"❌ Помилка при запиті до бази: {e}")

async def main():
    # Перед запуском видаляємо вебхуки, щоб уникнути ConflictError
    await bot.delete_webhook(drop_pending_updates=True)
    print("✅ Бот запущений анонімно та з'єднаний з БД!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот зупинений.")
