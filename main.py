import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 1. КОНФІГУРАЦІЯ
TOKEN = "8190360942:AAGiKEu3kbGJXv1VunH_75StcOlezCHCgBw"
# Формат: postgresql+asyncpg://користувач:пароль@хост/назва_бази
DB_URL = "postgresql+asyncpg://postgres:a02a87a91A@db.alefycnhibdovbyodwcb.supabase.co:5432/postgres"

# Створюємо "двигун" для бази даних
engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- ФУНКЦІЯ ПОШУКУ В БД ---
async def get_consumers_from_db(search_query: str):
    async with async_session() as session:
        # Шукаємо за частковим співпадінням імені (ILIKE - реєстронезалежний пошук)
        sql = text("SELECT id, name, debt_amount, cutoff_date FROM consumers WHERE name ILIKE :q")
        result = await session.execute(sql, {"q": f"%{search_query}%"})
        return result.all()

# --- INLINE ПОШУК (Пункт 9 ТЗ) ---
@dp.inline_query()
async def search_consumer(inline_query: types.InlineQuery):
    query_text = inline_query.query.strip()
    if not query_text:
        return

    # Отримуємо реальні дані з PostgreSQL
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
                                 f"📅 Дата відключення: {row.cutoff_date}"
                )
            )
        )
    await inline_query.answer(results, cache_time=1)

async def main():
    print("Бот запущений і підключений до БД...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())