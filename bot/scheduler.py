import logging
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import settings
from bot.content import stubs
from bot.keyboards.checkin_kb import sleep_duration_kb
from bot.states.checkin_states import EveningCheckin, MorningCheckin

logger = logging.getLogger(__name__)


async def send_morning_reminder(bot: Bot, scheduler_storage) -> None:
    user_id = settings.admin_user_id
    state = FSMContext(
        storage=scheduler_storage,
        key=StorageKey(chat_id=user_id, user_id=user_id, bot_id=bot.id),
    )
    await state.clear()
    await state.set_state(MorningCheckin.sleep_duration)
    await bot.send_message(
        chat_id=user_id,
        text=stubs.Q_MORNING_SLEEP_DURATION,
        reply_markup=sleep_duration_kb(),
    )
    logger.info("Ранкове нагадування надіслано.")


async def send_evening_reminder(bot: Bot, scheduler_storage) -> None:
    user_id = settings.admin_user_id
    state = FSMContext(
        storage=scheduler_storage,
        key=StorageKey(chat_id=user_id, user_id=user_id, bot_id=bot.id),
    )
    await state.clear()
    await state.set_state(EveningCheckin.day_fact)
    await bot.send_message(
        chat_id=user_id,
        text=stubs.Q_EVENING_DAY_FACT,
    )
    logger.info("Вечірнє нагадування надіслано.")


def setup_scheduler(bot: Bot, storage) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    # Щоранку о 09:00
    scheduler.add_job(
        send_morning_reminder,
        trigger="cron",
        hour=9,
        minute=0,
        args=[bot, storage],
    )

    # Щовечора о 21:00
    scheduler.add_job(
        send_evening_reminder,
        trigger="cron",
        hour=21,
        minute=0,
        args=[bot, storage],
    )

    return scheduler