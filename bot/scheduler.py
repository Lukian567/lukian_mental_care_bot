import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.db.base import async_session
from bot.db.repository import get_users_for_reminder

logger = logging.getLogger(__name__)

SUPPORTED_TIMEZONES = ["Europe/Warsaw", "Europe/Kyiv"]


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


async def check_and_send_scheduled_reminders(bot: Bot):
    """
    Щохвилинна перевірка та розсилка персональних нагадувань.
    Визначає поточний локальний час у кожній таймзоні та відправляє сповіщення
    користувачам із відповідним графіком.
    """
    for tz_name in SUPPORTED_TIMEZONES:
        try:
            now = datetime.now(ZoneInfo(tz_name))
            current_time_str = now.strftime("%H:%M")
        except Exception as e:
            logger.error("Помилка отримання часу для таймзони %s: %s", tz_name, e)
            continue

        # 🌅 Ранкові нагадування
        try:
            async with async_session() as session:
                morning_users = await get_users_for_reminder(
                    session=session,
                    timezone=tz_name,
                    target_time=current_time_str,
                    period="morning",
                )

            for user in morning_users:
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
        except Exception as e:
            logger.error(
                "Помилка вибірки користувачів для ранкового нагадування (%s, %s): %s",
                tz_name,
                current_time_str,
                e,
            )

        # 🌙 Вечірні нагадування
        try:
            async with async_session() as session:
                evening_users = await get_users_for_reminder(
                    session=session,
                    timezone=tz_name,
                    target_time=current_time_str,
                    period="evening",
                )

            for user in evening_users:
                try:
                    await bot.send_message(
                        chat_id=user.telegram_user_id,
                        text=(
                            "🌙 **Добрий вечір!**\n\n"
                            "Час для вечірнього підсумку: зафіксуй факти дня, "
                            "переважні емоції та підбий підсумки."
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
        except Exception as e:
            logger.error(
                "Помилка вибірки користувачів для вечірнього нагадування (%s, %s): %s",
                tz_name,
                current_time_str,
                e,
            )


def setup_scheduler(bot: Bot, dp: Dispatcher = None) -> AsyncIOScheduler:
    """Ініціалізує та конфігурує задачі планувальника."""
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        check_and_send_scheduled_reminders,
        trigger=CronTrigger(minute="*"),
        args=[bot],
        id="check_dynamic_reminders",
        replace_existing=True,
    )

    return scheduler