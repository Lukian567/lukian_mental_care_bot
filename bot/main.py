import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import settings
from bot.db.base import Base, engine
import bot.db.models  # регистрирует таблицы
from bot.routers import evening, morning
from bot.scheduler import setup_scheduler


async def init_db() -> None:
    """Создаем таблицы в базе, если они отсутствуют."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    logging.info("Проверяем структуру базы данных...")
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Подключаем роутеры команд
    dp.include_router(morning.router)
    dp.include_router(evening.router)

    # Инициализируем и запускаем фоновый планировщик
    scheduler = setup_scheduler(bot, dp.storage)
    scheduler.start()
    logging.info("Планировщик APScheduler успешно запущен.")

    logging.info("Бот готов к работе и ожидает сообщений...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())