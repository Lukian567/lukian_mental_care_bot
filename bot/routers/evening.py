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
    scale_kb,
    evening_fact_kb,
    action_done_kb,
    contact_quality_kb,
    emotion_kb,
    compassion_kb,
)
from bot.states.checkin_states import EveningCheckin

router = Router()
logger = logging.getLogger(__name__)


# 1. Старт чекіну (/evening) -> Факт дня
@router.message(Command("evening"))
async def cmd_evening(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(EveningCheckin.day_fact)
    await message.answer(
        stubs.Q_EVENING_DAY_FACT,
        reply_markup=evening_fact_kb(),
    )


# 2. Факт дня (кнопка) -> Настрій
@router.callback_query(EveningCheckin.day_fact, F.data.startswith("fact:"))
async def process_fact_btn(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "custom":
        await callback.message.edit_text("Опиши коротко, що сьогодні реально відбулося:")
        await callback.answer()
        return

    fact_map = {
        "bed": stubs.FACT_BED,
        "base": stubs.FACT_BASE,
        "out": stubs.FACT_OUT,
        "prod": stubs.FACT_PRODUCTIVE,
        "nothing": stubs.FACT_NOTHING,
    }
    await state.update_data(day_fact=fact_map.get(action, action))
    await state.set_state(EveningCheckin.mood_score)
    await callback.message.edit_text(
        stubs.Q_EVENING_MOOD,
        reply_markup=scale_kb("e_mood"),
    )
    await callback.answer()


# 2а. Факт дня (введено вручну текстом) -> Настрій
@router.message(EveningCheckin.day_fact)
async def process_fact_text(message: Message, state: FSMContext):
    await state.update_data(day_fact=message.text)
    await state.set_state(EveningCheckin.mood_score)
    await message.answer(
        stubs.Q_EVENING_MOOD,
        reply_markup=scale_kb("e_mood"),
    )


# 3. Настрій -> Статус виконання мікро-дії
@router.callback_query(EveningCheckin.mood_score, F.data.startswith("e_mood:"))
async def process_evening_mood(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.split(":")[1])
    await state.update_data(mood_score=score)
    await state.set_state(EveningCheckin.action_done)
    await callback.message.edit_text(
        stubs.Q_EVENING_ACTION_DONE,
        reply_markup=action_done_kb(),
    )
    await callback.answer()


# 4. Статус дії -> Контакт з людьми
@router.callback_query(EveningCheckin.action_done, F.data.startswith("done:"))
async def process_action_done(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    done_map = {
        "yes": stubs.STATUS_DONE,
        "part": stubs.STATUS_PARTIAL,
        "no": stubs.STATUS_FAIL,
        "none": stubs.STATUS_NO_PLAN,
    }
    await state.update_data(action_done=done_map.get(action, action))
    await state.set_state(EveningCheckin.contact_quality)
    await callback.message.edit_text(
        stubs.Q_EVENING_CONTACT_QUALITY,
        reply_markup=contact_quality_kb(),
    )
    await callback.answer()


# 5. Контакт (кнопка) -> Переважна емоція
@router.callback_query(EveningCheckin.contact_quality, F.data.startswith("contact:"))
async def process_contact_btn(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "custom":
        await callback.message.edit_text("Опиши свій контакт із людьми сьогодні повідомленням:")
        await callback.answer()
        return

    contact_map = {
        "good": stubs.CONTACT_GOOD,
        "work": stubs.CONTACT_WORK,
        "alone": stubs.CONTACT_ALONE_IN_CROWD,
        "avoid": stubs.CONTACT_AVOIDED,
        "skip": "Пропущено",
    }
    await state.update_data(contact_quality=contact_map.get(action, action))
    await state.set_state(EveningCheckin.emotion)
    await callback.message.edit_text(
        stubs.Q_EVENING_EMOTION,
        reply_markup=emotion_kb(),
    )
    await callback.answer()


# 5а. Контакт (текстом) -> Переважна емоція
@router.message(EveningCheckin.contact_quality)
async def process_contact_text(message: Message, state: FSMContext):
    await state.update_data(contact_quality=message.text)
    await state.set_state(EveningCheckin.emotion)
    await message.answer(
        stubs.Q_EVENING_EMOTION,
        reply_markup=emotion_kb(),
    )


# 6. Емоція -> Її інтенсивність (або одразу до підтримки, якщо пропуск)
@router.callback_query(EveningCheckin.emotion, F.data.startswith("emo:"))
async def process_emotion(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "skip":
        await state.update_data(emotion="Пропущено", emotion_intensity=None)
        await state.set_state(EveningCheckin.compassion)
        await callback.message.edit_text(
            stubs.Q_EVENING_COMPASSION,
            reply_markup=compassion_kb(),
        )
        await callback.answer()
        return

    emo_map = {
        "sadness": stubs.EMO_SADNESS,
        "anxiety": stubs.EMO_ANXIETY,
        "anger": stubs.EMO_ANGER,
        "guilt": stubs.EMO_GUILT,
        "emptiness": stubs.EMO_EMPTINESS,
        "calm": stubs.EMO_CALM,
    }
    await state.update_data(emotion=emo_map.get(action, action))
    await state.set_state(EveningCheckin.emotion_intensity)
    await callback.message.edit_text(
        stubs.Q_EVENING_EMOTION_INTENSITY,
        reply_markup=scale_kb("e_intensity"),
    )
    await callback.answer()


# 7. Інтенсивність емоції -> Самопідтримка
@router.callback_query(EveningCheckin.emotion_intensity, F.data.startswith("e_intensity:"))
async def process_emotion_intensity(callback: CallbackQuery, state: FSMContext):
    score = int(callback.data.split(":")[1])
    await state.update_data(emotion_intensity=score)
    await state.set_state(EveningCheckin.compassion)
    await callback.message.edit_text(
        stubs.Q_EVENING_COMPASSION,
        reply_markup=compassion_kb(),
    )
    await callback.answer()


# 8. Фінал: Самопідтримка (кнопка) -> Збереження та ВИДАЛЕННЯ кнопок
@router.callback_query(EveningCheckin.compassion, F.data.startswith("comp:"))
async def process_compassion_btn(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]

    if action == "custom":
        await callback.message.edit_text("Що б ти сказав(-ла) другові? Напиши повідомленням:")
        await callback.answer()
        return

    comp_map = {
        "best": stubs.COMPASSION_BEST,
        "normal": stubs.COMPASSION_NORMAL,
        "enough": stubs.COMPASSION_ENOUGH,
        "tomorrow": stubs.COMPASSION_TOMORROW,
        "skip": "Пропущено",
    }
    await state.update_data(compassion=comp_map.get(action, action))
    await callback.answer()

    # Зберігаємо в базу і ПЕРЕПИСУЄМО повідомлення, щоб кнопки зникли!
    try:
        data = await state.get_data()
        today = datetime.now(ZoneInfo(settings.timezone)).date()

        async with async_session() as session:
            await save_checkin(
                session=session,
                user_id=callback.from_user.id,
                checkin_date=today,
                period="evening",
                data=data,
            )

        await state.clear()
        # Ось тут замість answer використовуємо edit_text
        await callback.message.edit_text(stubs.EVENING_COMPLETE_MSG)
    except Exception as e:
        logger.exception("Помилка збереження вечірнього чекіну: %s", e)
        await callback.message.answer(f"Помилка при збереженні: {e}")


# 8а. Фінал: Самопідтримка (якщо введено вручну текстом)
@router.message(EveningCheckin.compassion)
async def process_compassion_text(message: Message, state: FSMContext):
    await state.update_data(compassion=message.text)
    try:
        data = await state.get_data()
        today = datetime.now(ZoneInfo(settings.timezone)).date()

        async with async_session() as session:
            await save_checkin(
                session=session,
                user_id=message.from_user.id,
                checkin_date=today,
                period="evening",
                data=data,
            )

        await state.clear()
        await message.answer(stubs.EVENING_COMPLETE_MSG)
    except Exception as e:
        logger.exception("Помилка збереження вечірнього чекіну: %s", e)
        await message.answer(f"Помилка при збереженні: {e}")