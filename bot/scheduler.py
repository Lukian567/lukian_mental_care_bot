import logging
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.db.base import async_session
from bot.db.repository import get_active_users_by_timezone

logger = logging.getLogger(__name__)


def morning_reminder_kb() -> InlineKeyboardMarkup:
    """Кнопка швидкого старту ранкового чекіну прямо з нагадування."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Розпочати чекін", callback_data="start_morning")]
        ]
    )


def evening_reminder_kb() -> InlineKeyboardMarkup:
    """Кнопка швидкого старту вечірнього чекіну прямо з нагадування."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌙 Розпочати чекін", callback_data="start_evening")]
        ]
    )


async def send_morning_reminders(bot: Bot, timezone: str):
    """Розсилка ранкового нагадування о 08:00 за локальним часом."""
    logger.info("Запуск ранкових нагадувань для часового поясу: %s", timezone)
    async with async_session() as session:
        users = await get_active_users_by_timezone(session, timezone)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_user_id,
                text=(
                    "🌅 **Доброго ранку!**\n\n"
                    "Час для ранкового чекіну: зафіксуй якість сну, "
                    "рівень ресурсу та намір на день."
                ),
                reply_markup=morning_reminder_kb(),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(
                "Не вдалося доставити ранкове нагадування користувачу %s: %s",
                user.telegram_user_id,
                e,
            )


async def send_evening_reminders(bot: Bot, timezone: str):
    """Розсилка вечірнього нагадування о 22:00 за локальним часом."""
    logger.info("Запуск вечірніх нагадувань для часового поясу: %s", timezone)
    async with async_session() as session:
        users = await get_active_users_by_timezone(session, timezone)

    for user in users:
        try:
            await bot.send_message(
                chat_id=user.telegram_user_id,
                text=(
                    "🌙 **Добрий вечір!**\n\n"
                    "Час для вечірнього підсумку: зафіксуй факти дня, "
                    "переважні емоції та скажи собі слова підтримки."
                ),
                reply_markup=evening_reminder_kb(),
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.warning(
                "Не вдалося доставити вечірнє нагадування користувачу %s: %s",
                user.telegram_user_id,
                e,
            )


def setup_scheduler(bot: Bot, dp: Dispatcher = None) -> AsyncIOScheduler:
    """Ініціалізує та конфігурує задачі планувальника."""
    scheduler = AsyncIOScheduler()

    # 🇵🇱 1. Польща (Europe/Warsaw): 08:00 та 22:00
    scheduler.add_job(
        send_morning_reminders,
        trigger=CronTrigger(hour=8, minute=0, timezone="Europe/Warsaw"),
        args=[bot, "Europe/Warsaw"],
        id="morning_reminder_warsaw",
        replace_existing=True,
    )
    scheduler.add_job(
        send_evening_reminders,
        trigger=CronTrigger(hour=22, minute=0, timezone="Europe/Warsaw"),
        args=[bot, "Europe/Warsaw"],
        id="evening_reminder_warsaw",
        replace_existing=True,
    )

    # 🇺🇦 2. Україна (Europe/Kyiv): 08:00 та 22:00
    scheduler.add_job(
        send_morning_reminders,
        trigger=CronTrigger(hour=8, minute=0, timezone="Europe/Kyiv"),
        args=[bot, "Europe/Kyiv"],
        id="morning_reminder_kyiv",
        replace_existing=True,
    )
    scheduler.add_job(
        send_evening_reminders,
        trigger=CronTrigger(hour=22, minute=0, timezone="Europe/Kyiv"),
        args=[bot, "Europe/Kyiv"],
        id="evening_reminder_kyiv",
        replace_existing=True,
    )

    return scheduler