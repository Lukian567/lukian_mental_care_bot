import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.config import settings
from bot.content import stubs
from bot.db.base import async_session
from bot.db.repository import save_checkin
from bot.keyboards.checkin_kb import (
    sleep_duration_kb,
    scale_kb,
    morning_thought_kb,
    morning_action_kb,
)
from bot.states.checkin_states import MorningCheckin

router = Router()
logger = logging.getLogger(__name__)


# 1. Старт чекіну (/morning) -> Сон
@router.message(Command("morning"))
async def cmd_morning(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(MorningCheckin.sleep_duration)
    await message.answer(
        stubs.Q_MORNING_SLEEP_DURATION,
        reply_markup=sleep_duration_kb(),
    )


# 2. Тривалість сну -> Якість сну
@router.callback_query(MorningCheckin.sleep_duration, F.data.startswith("sleep_dur:"))
async def process_sleep_duration(callback: CallbackQuery, state: FSMContext):
    minutes = int(callback.data.split(":")[1])
    await state.update_data(sleep_duration_minutes=minutes)
    await state.set_state(MorningCheckin.sleep_quality)
    await callback.message.edit_text(
        stubs.Q_MORNING_SLEEP_QUALITY,
        reply_markup=scale_kb("m_sleep_q"),
    )
    await callback.answer()


# 3. Якість сну -> Настрій
@router.callback_query(MorningCheckin.sleep_quality, F.data.startswith("m_sleep_q:"))
async def process_sleep_quality(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.split(":")[1])
    await state.update_data(sleep_quality=score)
    await state.set_state(MorningCheckin.mood)
    await callback.message.edit_text(
        stubs.Q_MORNING_MOOD,
        reply_markup=scale_kb("m_mood"),
    )
    await callback.answer()


# 4. Настрій -> Опір/важкість підйому
@router.callback_query(MorningCheckin.mood, F.data.startswith("m_mood:"))
async def process_morning_mood(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.split(":")[1])
    await state.update_data(morning_mood=score)
    await state.set_state(MorningCheckin.resistance)
    await callback.message.edit_text(
        stubs.Q_MORNING_RESISTANCE,
        reply_markup=scale_kb("m_resist"),
    )
    await callback.answer()


# 5. Опір -> Тривожність
@router.callback_query(MorningCheckin.resistance, F.data.startswith("m_resist:"))
async def process_resistance(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.split(":")[1])
    await state.update_data(resistance_level=score)
    await state.set_state(MorningCheckin.anxiety)
    await callback.message.edit_text(
        stubs.Q_MORNING_ANXIETY,
        reply_markup=scale_kb("m_anxiety"),
    )
    await callback.answer()


# 6. Тривожність -> Автоматична думка
@router.callback_query(MorningCheckin.anxiety, F.data.startswith("m_anxiety:"))
async def process_anxiety(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.split(":")[1])
    await state.update_data(anxiety_level=score)
    await state.set_state(MorningCheckin.thought)
    await callback.message.edit_text(
        stubs.Q_MORNING_THOUGHT,
        reply_markup=morning_thought_kb(),
    )
    await callback.answer()


# 7. Думка (вибір кнопки)
@router.callback_query(MorningCheckin.thought, F.data.startswith("thought:"))
async def process_thought_btn(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "custom":
        await callback.message.edit_text("Напиши свою першу думку повідомленням:")
        await callback.answer()
        return

    thought_map = {
        "again": stubs.THOUGHT_AGAIN,
        "nothing": stubs.THOUGHT_NOTHING,
        "better": stubs.THOUGHT_BETTER,
        "task": stubs.THOUGHT_TASK,
        "neutral": stubs.THOUGHT_NEUTRAL,
        "skip": "Пропущено",
    }
    await state.update_data(morning_thought=thought_map.get(action, action))
    await state.set_state(MorningCheckin.micro_action)
    await callback.message.edit_text(
        stubs.Q_MORNING_MICRO_ACTION,
        reply_markup=morning_action_kb(),
    )
    await callback.answer()


# 7а. Думка (текстом)
@router.message(MorningCheckin.thought)
async def process_thought_text(message: Message, state: FSMContext):
    await state.update_data(morning_thought=message.text)
    await state.set_state(MorningCheckin.micro_action)
    await message.answer(
        stubs.Q_MORNING_MICRO_ACTION,
        reply_markup=morning_action_kb(),
    )


# 8. Фінал: Мікро-дія (вибір кнопки)
@router.callback_query(MorningCheckin.micro_action, F.data.startswith("action:"))
async def process_action_btn(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "custom":
        await callback.message.edit_text("Напиши свою мікро-дію на сьогодні повідомленням:")
        await callback.answer()
        return

    action_map = {
        "self_care": stubs.ACTION_SELF_CARE,
        "walk": stubs.ACTION_WALK,
        "work": stubs.ACTION_STUDY_WORK,
        "survive": stubs.ACTION_SURVIVE,
        "skip": "Без плану",
    }
    await state.update_data(micro_action=action_map.get(action, action))
    await callback.answer()
    
    # Редагуємо повідомлення на фінальне
    try:
        data = await state.get_data()
        today = datetime.now(ZoneInfo(settings.timezone)).date()

        async with async_session() as session:
            await save_checkin(
                session=session,
                user_id=callback.from_user.id,
                checkin_date=today,
                period="morning",
                data=data,
            )

        await state.clear()
        await callback.message.edit_text(stubs.MORNING_COMPLETE_MSG)
    except Exception as e:
        logger.exception("Помилка збереження ранкового чекіну: %s", e)
        await callback.message.answer(f"Помилка при збереженні: {e}")


# 8а. Фінал: Мікро-дія (текстом)
@router.message(MorningCheckin.micro_action)
async def process_action_text(message: Message, state: FSMContext):
    await state.update_data(micro_action=message.text)
    try:
        data = await state.get_data()
        today = datetime.now(ZoneInfo(settings.timezone)).date()

        async with async_session() as session:
            await save_checkin(
                session=session,
                user_id=message.from_user.id,
                checkin_date=today,
                period="morning",
                data=data,
            )

        await state.clear()
        await message.answer(stubs.MORNING_COMPLETE_MSG)
    except Exception as e:
        logger.exception("Помилка збереження ранкового чекіну: %s", e)
        await message.answer(f"Помилка при збереженні: {e}")