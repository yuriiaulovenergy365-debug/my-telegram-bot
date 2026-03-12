import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# --- 1. ПРЯМА КОНФІГУРАЦІЯ (ВСТАВТЕ ВАШІ ДАНІ ТУТ) ---
TOKEN = "8190360942:AAGiKEu3kbGJXv1VunH_75StcOlezCHCgBw"
# У рядку нижче замініть [ВАШ_ПАРОЛЬ] на реальний пароль від Supabase
DB_URL = "postgresql+asyncpg://postgres:a02a87a91@db.alefycnhibdovbyodwcb.supabase.co:5432/postgres"

# Перевірка на випадок, якщо забули вставити дані
if "ВАШ_" in TOKEN or "[ВАШ_ПАРОЛЬ]" in DB_URL:
    print("❌ ПОМИЛКА: Ви не вставили реальний Токен або Пароль у код!")
    exit(1)

# --- 2. НАЛАШТУВАННЯ БАЗИ ДАНИХ ---
engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- 3. ФУНКЦІЯ ПОШУКУ В БД ---
async def get_consumers_from_db(search_query: str):
    async with async_session() as session:
        # Шукаємо за частковим співпадінням імені (ILIKE - реєстронезалежний пошук)
        # Таблиця має називатися 'consumers'
        sql = text("SELECT id, name, debt_amount, cutoff_date FROM consumers WHERE name ILIKE :q")
        result = await session.execute(sql, {"q": f"%{search_query}%"})
        return result.all()

# --- 4. INLINE ПОШУК (Пункт 9 ТЗ) ---
@dp.inline_query()
async def search_consumer(inline_query: types.InlineQuery):
    query_text = inline_query.query.strip()
    if not query_text:
        return

    try:
        # Отримуємо дані з PostgreSQL (Supabase)
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
        # Відправляємо результати користувачу
        await inline_query.answer(results, cache_time=1)
    except Exception as e:
        print(f"❌ Помилка при запиті до бази: {e}")

async def main():
    print("✅ Бот запущений і успішно з'єднаний з Supabase!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот зупинений.")
