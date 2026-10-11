from datetime import date
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.db.base import async_session
from bot.db.repository import save_morning_checkin, get_user
from bot.keyboards.checkin_kb import (
    sleep_hours_kb,
    sleep_quality_kb,
    morning_mood_kb,
    morning_resistance_kb,
    morning_anxiety_kb,
    morning_thought_kb,
    morning_action_kb,
)
from bot.states.checkin_states import MorningCheckin

router = Router()

SLEEP_LABEL_MAP = {
    "5.5": "< 6 год",
    "6.5": "6–7 год",
    "7.5": "7–8 год",
    "8.5": "8–9 год",
    "9.5": "> 9 год",
}

THOUGHT_MAP = {
    "tasks": "📋 Завдання",
    "anxiety": "⚡ Тривожні очікування",
    "rumination": "🔄 Румінація / вчорашнє",
    "fog": "🌫 Ментальний туман",
    "calm": "🧘 Спокійна ясна голова",
    "drive": "🔥 Драйв / очікування",
}

ACTION_MAP = {
    "task": "🎯 Закрити ключову робочу/навчальну задачу",
    "social": "👥 Соціальний контакт / зустріч / дзвінок",
    "workout": "🏋️ Провести тренування / фізичну активність",
    "walk": "🚶 Прогулянка / зміна середовища",
    "order": "🧹 Навести лад у просторі",
    "rest": "🛋 Свідомо відпочити без почуття провини",
    "no_plan": "⚪ День без плану / спостереження",
}


# -------------------------------------------------------------
# Крок 1.1: Тривалість сну
# -------------------------------------------------------------
@router.message(Command("morning"))
async def cmd_morning(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(MorningCheckin.sleep_hours)
    await message.answer(
        "🌅 **Ранковий протокол (1/6)**\n\n"
        "Скільки тривав сон?",
        reply_markup=sleep_hours_kb(),
        parse_mode="Markdown",
    )


@router.callback_query(F.data.startswith("sleep_h:"))
async def process_sleep_hours(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]
    if val == "custom":
        await state.set_state(MorningCheckin.sleep_hours_custom)
        await callback.message.edit_text(
            "✍️ Введи точну тривалість сну в годинах (наприклад: `7.5` або `8`):",
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    hours = float(val)
    label = SLEEP_LABEL_MAP.get(val, f"{hours} год")
    await state.update_data(sleep_hours=hours, sleep_display=label)
    await state.set_state(MorningCheckin.sleep_quality)

    await callback.message.edit_text(
        f"✅ Сон: **{label}**\n\n"
        "Яка суб'єктивна якість сну?\n\n"
        "(1 — поганий / не відновлювальний\n 5 — повністю відновився ⚡)",
        reply_markup=sleep_quality_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(MorningCheckin.sleep_hours_custom, ~F.text.startswith("/"))
async def process_sleep_hours_custom(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        hours = float(text)
        if not (1.0 <= hours <= 24.0):
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Будь ласка, введи коректне число від 1 до 24 (наприклад, 7.5):")
        return

    label = f"{hours} год"
    await state.update_data(sleep_hours=hours, sleep_display=label)
    await state.set_state(MorningCheckin.sleep_quality)
    await message.answer(
        f"✅ Сон: **{label}**\n\n"
        "Яка суб'єктивна якість сну?\n\n"
        "(1 — поганий / не відновлювальний\n 5 — повністю відновився ⚡)",
        reply_markup=sleep_quality_kb(),
        parse_mode="Markdown",
    )


# -------------------------------------------------------------
# Крок 1.2: Якість сну -> Крок 2: Ранковий настрій
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("sleep_q:"))
async def process_sleep_quality(callback: CallbackQuery, state: FSMContext):
    q = int(callback.data.split(":")[1])
    await state.update_data(sleep_quality=q)
    await state.set_state(MorningCheckin.morning_mood)

    await callback.message.edit_text(
        "🌅 **Ранковий протокол (2/6)**\n\n"
        "Який емоційний стан на старті дня?\n\n"
        "(1 — важкий / пригнічений 📉\n 5 — ресурсний / піднесений 🚀)",
        reply_markup=morning_mood_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# -------------------------------------------------------------
# Крок 2 -> Крок 3: Рівень внутрішнього опору
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("m_mood:"))
async def process_morning_mood(callback: CallbackQuery, state: FSMContext):
    mood = int(callback.data.split(":")[1])
    await state.update_data(morning_mood=mood)
    await state.set_state(MorningCheckin.morning_resistance)

    await callback.message.edit_text(
        "🌅 **Ранковий протокол (3/6)**\n\n"
        "Наскільки важко було зібрати сили та розпочати день?\n\n"
        "(1 — взагалі без зусиль 🟢\n 5 — колосальний опір 🛑)",
        reply_markup=morning_resistance_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# -------------------------------------------------------------
# Крок 3 -> Крок 4: Фонова тривожність
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("m_res:"))
async def process_morning_resistance(callback: CallbackQuery, state: FSMContext):
    res = int(callback.data.split(":")[1])
    await state.update_data(morning_resistance=res)
    await state.set_state(MorningCheckin.morning_anxiety)

    await callback.message.edit_text(
        "🌅 **Ранковий протокол (4/6)**\n\n"
        "Рівень внутрішнього напруження або тривоги:\n\n"
        "(1 — спокій / відсутність тривоги 🧘\n 5 — висока тривожність / напруга ⚡)",
        reply_markup=morning_anxiety_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# -------------------------------------------------------------
# Крок 4 -> Крок 5: Ранкова думка (Когнітивний фокус)
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("m_anx:"))
async def process_morning_anxiety(callback: CallbackQuery, state: FSMContext):
    anx = int(callback.data.split(":")[1])
    await state.update_data(morning_anxiety=anx)
    await state.set_state(MorningCheckin.morning_thought)

    await callback.message.edit_text(
        "🌅 **Ранковий протокол (5/6)**\n\n"
        "Яка головна думка або фокус уваги зараз у голові?\n\n"
        "(Обери варіант нижче або напиши свій текстом)",
        reply_markup=morning_thought_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# -------------------------------------------------------------
# Крок 5: Обробка кнопок думок
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("thought_p:"))
async def process_thought_pattern(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "custom":
        await state.set_state(MorningCheckin.morning_thought_custom)
        await callback.message.edit_text("✍️ Запиши коротко свою головну думку на старті дня:", parse_mode="Markdown")
        await callback.answer()
        return

    thought_val = None if val == "skip" else THOUGHT_MAP.get(val, val)
    await state.update_data(morning_thought=thought_val)
    await state.set_state(MorningCheckin.morning_action)

    await callback.message.edit_text(
        "🌅 **Ранковий протокол (6/6)**\n\n"
        "Обери один конкретний фокус / мікро-дію на день:",
        reply_markup=morning_action_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(MorningCheckin.morning_thought, ~F.text.startswith("/"))
@router.message(MorningCheckin.morning_thought_custom, ~F.text.startswith("/"))
async def process_thought_text(message: Message, state: FSMContext):
    thought = message.text.strip()
    await state.update_data(morning_thought=thought)
    await state.set_state(MorningCheckin.morning_action)

    await message.answer(
        "🌅 **Ранковий протокол (6/6)**\n\n"
        "Обери один конкретний фокус / мікро-дію на день:",
        reply_markup=morning_action_kb(),
        parse_mode="Markdown",
    )


# -------------------------------------------------------------
# Крок 6: Поведінковий якір дня + Фінал
# -------------------------------------------------------------
async def complete_morning_checkin(target, state: FSMContext, anchor_text: str):
    data = await state.get_data()
    user_id = target.from_user.id
    today = date.today()

    thought_val = data.get("morning_thought")
    sleep_display = data.get("sleep_display") or f"{data.get('sleep_hours', 7.0)} год"

    evening_time = None
    try:
        async with async_session() as session:
            await save_morning_checkin(
                session=session,
                telegram_user_id=user_id,
                checkin_date=today,
                sleep_hours=data.get("sleep_hours", 7.0),
                sleep_quality=data.get("sleep_quality", 3),
                morning_mood=data.get("morning_mood", 3),
                morning_resistance=data.get("morning_resistance", 1),
                morning_anxiety=data.get("morning_anxiety", 1),
                morning_thought_pattern="Думка" if thought_val else None,
                morning_thought_custom=thought_val,
                morning_action_anchor=anchor_text,
                raw_payload=data,
            )
            user_obj = await get_user(session, user_id)
            if user_obj and getattr(user_obj, "evening_reminder_time", None):
                evening_time = user_obj.evening_reminder_time
    except Exception as e:
        print("Save morning checkin error:", e)

    await state.clear()

    farewell = (
        f"До зустрічі під час вечірнього протоколу о **{evening_time}**! 🚀"
        if evening_time
        else "До зустрічі під час вечірнього підсумку! 🚀"
    )

    summary_text = (
        "✨ **Ранковий протокол збережено!**\n\n"
        f"• Сон: **{sleep_display}** (якість: {data.get('sleep_quality')}/5)\n"
        f"• Настрій: **{data.get('morning_mood')}/5** | Опір: **{data.get('morning_resistance')}/5**\n"
        f"• Тривожність: **{data.get('morning_anxiety')}/5**\n"
        f"• Думка: **{thought_val or '—'}**\n"
        f"• Якір дня: **{anchor_text}**\n\n"
        f"Вдалого дня! {farewell}"
    )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(summary_text, parse_mode="Markdown")
        await target.answer()
    else:
        await target.answer(summary_text, parse_mode="Markdown")


@router.callback_query(F.data.startswith("anchor:"))
async def process_morning_action(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "custom":
        await state.set_state(MorningCheckin.morning_action_custom)
        await callback.message.edit_text("✍️ Напиши свою конкретну дію на день:", parse_mode="Markdown")
        await callback.answer()
        return

    anchor_text = ACTION_MAP.get(val, "⚪ День без плану / спостереження")
    await complete_morning_checkin(callback, state, anchor_text)


@router.message(MorningCheckin.morning_action_custom, ~F.text.startswith("/"))
async def process_morning_action_custom(message: Message, state: FSMContext):
    anchor_text = message.text.strip()
    await complete_morning_checkin(message, state, anchor_text)


# -------------------------------------------------------------
# Обробник універсального повернення «« Назад» на 1 крок
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("m_back:"))
async def process_morning_back(callback: CallbackQuery, state: FSMContext):
    target_step = callback.data.split(":")[1]
    data = await state.get_data()

    if target_step == "1":
        await state.set_state(MorningCheckin.sleep_hours)
        await callback.message.edit_text(
            "🌅 **Ранковий протокол (1/6)**\n\n"
            "Скільки тривав сон?",
            reply_markup=sleep_hours_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "2":
        await state.set_state(MorningCheckin.sleep_quality)
        label = data.get("sleep_display") or f"{data.get('sleep_hours', 7.0)} год"
        await callback.message.edit_text(
            f"✅ Сон: **{label}**\n\n"
            "Яка суб'єктивна якість сну?\n\n"
            "(1 — поганий / не відновлювальний\n 5 — повністю відновився ⚡)",
            reply_markup=sleep_quality_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "3":
        await state.set_state(MorningCheckin.morning_mood)
        await callback.message.edit_text(
            "🌅 **Ранковий протокол (2/6)**\n\n"
            "Який емоційний стан на старті дня?\n\n"
            "(1 — важкий / пригнічений 📉\n 5 — ресурсний / піднесений 🚀)",
            reply_markup=morning_mood_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "4":
        await state.set_state(MorningCheckin.morning_resistance)
        await callback.message.edit_text(
            "🌅 **Ранковий протокол (3/6)**\n\n"
            "Наскільки важко було зібрати сили та розпочати день?\n\n"
            "(1 — взагалі без зусиль 🟢\n 5 — колосальний опір 🛑)",
            reply_markup=morning_resistance_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "5":
        await state.set_state(MorningCheckin.morning_anxiety)
        await callback.message.edit_text(
            "🌅 **Ранковий протокол (4/6)**\n\n"
            "Рівень внутрішнього напруження або тривоги:\n\n"
            "(1 — спокій / відсутність тривоги 🧘\n 5 — висока тривожність / напруга ⚡)",
            reply_markup=morning_anxiety_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "6":
        await state.set_state(MorningCheckin.morning_thought)
        await callback.message.edit_text(
            "🌅 **Ранковий протокол (5/6)**\n\n"
            "Яка головна думка або фокус уваги зараз у голові?\n\n"
            "(Обери варіант нижче або напиши свій текстом)",
            reply_markup=morning_thought_kb(),
            parse_mode="Markdown",
        )

    await callback.answer()