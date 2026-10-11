import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from bot.config import settings
from bot.db.base import Base, engine
import bot.db.models
from bot.routers import common, morning, evening
from bot.scheduler import setup_scheduler


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def set_bot_commands(bot: Bot) -> None:
    """Реєструє системне меню команд Telegram (кнопка Menu і список при вводі /)."""
    # Базові команди для всіх користувачів
    commands = [
        BotCommand(command="start", description="Головне меню"),
        BotCommand(command="morning", description="Ранковий чекін"),
        BotCommand(command="evening", description="Вечірній чекін"),
        BotCommand(command="stats", description="Статистика за 7 днів"),
        BotCommand(command="cancel", description="Скасувати поточне опитування"),
        BotCommand(command="help", description="Довідка по боту"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

    # Додаткова адмінська команда для твого чату
    if settings.admin_user_id:
        admin_commands = commands + [
            BotCommand(command="export", description="📥 Експорт бази в CSV"),
        ]
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(chat_id=int(settings.admin_user_id)),
        )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    logging.info("Перевіряємо структуру бази даних...")
    await init_db()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Реєстрація роутерів (common обов'язково першим, щоб перехоплювати /cancel)
    dp.include_router(common.router)
    dp.include_router(morning.router)
    dp.include_router(evening.router)

    # Налаштовуємо спливаюче меню команд
    await set_bot_commands(bot)

    # Запуск фонового планувальника нагадувань
    scheduler = setup_scheduler(bot)
    scheduler.start()

    logging.info("Бот готовий до роботи. Запускаємо polling...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())