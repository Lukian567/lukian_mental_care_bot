from datetime import date
from typing import Optional

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.base import async_session
from bot.db.repository import (
    get_today_morning_anchor,
    save_evening_checkin,
)
from bot.keyboards.checkin_kb import (
    action_result_kb,
    activity_domains_kb,
    dominant_emotion_kb,
    emotion_intensity_kb,
    evening_mood_kb,
    social_state_kb,
    evening_gratitude_kb,
)
from bot.states.checkin_states import EveningCheckin

router = Router()

DOMAIN_LABEL_MAP = {
    "cognitive": "🧠 Когнітивна праця (навчання / робота)",
    "physical": "🏃 Фізична активність (тренування / рух)",
    "social": "👥 Соціальна взаємодія (зустрічі / спілкування)",
    "screen": "📱 Екранний час (скролінг / контент)",
    "rest": "🔋 Відновлення (тиша / сон / відпочинок)",
    "routine": "🧹 Побут (рутина / порядок)",
    "stress": "⚡ Гострі стресори (форс-мажор / тиск)",
}

ACTION_RESULT_LABEL_MAP = {
    "DONE": "✅ Так, повністю",
    "PARTIAL": "⏳ Частково",
    "MISSED": "❌ Не зробив(-ла)",
    "OBSTACLES": "🔄 Завадили обставини",
    "NO_PLAN_SET": "⚪ День був без плану",
}

SOCIAL_MAP = {
    "charge": "🔋 Додало сил / підняло настрій",
    "routine": "⚖️ Був серед людей — звичайна рутина",
    "drain": "🪫 Забрало сили / виснажило",
    "alienation": "👤 Був серед людей, але ніби сам",
    "solitude": "🧘 Побув наодинці — відновив сили",
    "alone_routine": "🏠 Побув(-ла) наодинці — звична нормальна рутина",
    "isolation_drained": "🚪 Був сам — це пригнітило / брак людей",
}

EMOTION_MAP = {
    "drive_joy": "🔥 Драйв / Радість",
    "calm_balance": "😌 Спокій / Баланс",
    "anxiety_tension": "⚡ Тривога / Напруга",
    "anger_irritation": "😡 Злість / Дратівливість",
    "sadness_down": "🌧 Сум / Пригніченість",
    "apathy_empty": "🪫 Апатія / Порожнеча",
    "guilt_shame": "😔 Провина / Сором",
}

GRATITUDE_MAP = {
    "coped": "🛋 Впорався(-лась) із цим днем",
    "discipline": "🎯 Дисципліна та конкретні кроки",
    "rest": "🔋 Час на перепочинок",
    "social": "🫂 Люди поруч / добрий вчинок",
}


# -------------------------------------------------------------
# Крок 1. Домени активності та навантаження (Мультиселект)
# -------------------------------------------------------------
@router.message(Command("evening"))
async def cmd_evening(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(EveningCheckin.activity_domains)
    await state.update_data(selected_domains=[], custom_activity_text=None)

    await message.answer(
        "🌙 **Вечірній протокол (1/7)**\n\n"
        "Куди сьогодні пішов час та енергія?\n\n"
        "(Обери категорії, які займали відчутну частину дня)",
        reply_markup=activity_domains_kb(selected_keys=[]),
        parse_mode="Markdown",
    )


@router.callback_query(EveningCheckin.activity_domains, F.data.startswith("dom_tog:"))
async def process_domain_toggle(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split(":")[1]
    data = await state.get_data()
    selected: list = data.get("selected_domains", [])

    if key in selected:
        selected.remove(key)
    else:
        selected.append(key)

    await state.update_data(selected_domains=selected)
    has_custom = bool(data.get("custom_activity_text"))

    await callback.message.edit_reply_markup(
        reply_markup=activity_domains_kb(selected_keys=selected, has_custom=has_custom)
    )
    await callback.answer()


@router.callback_query(EveningCheckin.activity_domains, F.data == "dom_custom")
async def process_domain_custom_ask(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EveningCheckin.activity_domains_custom)
    await callback.message.answer("✍️ Вкажи свій варіант текстом:")
    await callback.answer()


@router.message(EveningCheckin.activity_domains_custom, ~F.text.startswith("/"))
async def process_domain_custom_receive(message: Message, state: FSMContext):
    custom_text = message.text.strip()
    data = await state.get_data()
    selected = data.get("selected_domains", [])
    await state.update_data(custom_activity_text=custom_text)
    await state.set_state(EveningCheckin.activity_domains)

    await message.answer(
        f"✅ Додано: «{custom_text}»\n\n"
        "Можеш обрати ще пункти або натиснути **➡️ Зберегти вибір**:",
        reply_markup=activity_domains_kb(selected_keys=selected, has_custom=True),
        parse_mode="Markdown",
    )


@router.callback_query(EveningCheckin.activity_domains, F.data == "dom_save")
async def process_domain_save(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_domains", [])
    custom = data.get("custom_activity_text")

    if not selected and not custom:
        await callback.answer("⚠️ Обери хоча б один пункт або вкажи свій!", show_alert=True)
        return

    await state.set_state(EveningCheckin.evening_mood)
    await callback.message.edit_text(
        "🌙 **Вечірній протокол (2/7)**\n\n"
        "Який загальний настрій дня?\n\n"
        "(1 — негативний / важкий 📉\n 5 — позитивний / піднесений 🚀)",
        reply_markup=evening_mood_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# -------------------------------------------------------------
# Крок 2. Загальний настрій дня -> Крок 3 (Якір) або Крок 4 (Соціум)
# -------------------------------------------------------------
@router.callback_query(EveningCheckin.evening_mood, F.data.startswith("e_mood:"))
async def process_evening_mood(callback: CallbackQuery, state: FSMContext):
    mood = int(callback.data.split(":")[1])
    await state.update_data(evening_mood=mood)

    today = date.today()
    morning_anchor = None
    try:
        async with async_session() as session:
            morning_anchor = await get_today_morning_anchor(session, callback.from_user.id, today)
    except Exception:
        morning_anchor = None

    if not morning_anchor or "без плану" in morning_anchor.lower() or "no_plan" in morning_anchor.lower():
        await state.update_data(action_result="NO_PLAN_SET", morning_anchor="⚪ День без плану")
        await state.set_state(EveningCheckin.social_state)
        await callback.message.edit_text(
            "🌙 **Вечірній протокол (4/7)** *(ранковий якір був без плану — крок 3 пропущено)*\n\n"
            "Як сьогодні контакт із людьми вплинув на твої сили?",
            reply_markup=social_state_kb(),
            parse_mode="Markdown",
        )
    else:
        await state.update_data(morning_anchor=morning_anchor)
        await state.set_state(EveningCheckin.action_result)
        await callback.message.edit_text(
            "🌙 **Вечірній протокол (3/7)**\n\n"
            "Чи вдалося реалізувати заплановану дію?\n\n"
            f"🎯 Твій якір: **«{morning_anchor}»**",
            reply_markup=action_result_kb(),
            parse_mode="Markdown",
        )
    await callback.answer()


# -------------------------------------------------------------
# Крок 3. Верифікація ранкового наміру -> Крок 4: Соціальний баланс
# -------------------------------------------------------------
@router.callback_query(EveningCheckin.action_result, F.data.startswith("act_res:"))
async def process_action_result(callback: CallbackQuery, state: FSMContext):
    res = callback.data.split(":")[1]
    await state.update_data(action_result=res)
    await state.set_state(EveningCheckin.social_state)

    await callback.message.edit_text(
        "🌙 **Вечірній протокол (4/7)**\n\n"
        "Як сьогодні контакт із людьми вплинув на твої сили?",
        reply_markup=social_state_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# -------------------------------------------------------------
# Крок 4. Соціальний енергетичний баланс -> Крок 5: Домінуюча емоція
# -------------------------------------------------------------
@router.callback_query(EveningCheckin.social_state, F.data.startswith("soc:"))
async def process_social_state(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "custom":
        await state.set_state(EveningCheckin.social_custom)
        await callback.message.edit_text("✍️️ Опиши вплив людей текстом:", parse_mode="Markdown")
        await callback.answer()
        return

    soc_label = None if val == "skip" else SOCIAL_MAP.get(val, val)
    await state.update_data(social_state=soc_label, social_custom_text=None)
    await state.set_state(EveningCheckin.dominant_emotion)

    await callback.message.edit_text(
        "🌙 **Вечірній протокол (5/7)**\n\n"
        "Яка емоція переважала сьогодні?\n\n"
        "(Обери головний емоційний тон дня)",
        reply_markup=dominant_emotion_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(EveningCheckin.social_custom, ~F.text.startswith("/"))
async def process_social_custom(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(social_state="Власний опис", social_custom_text=text)
    await state.set_state(EveningCheckin.dominant_emotion)

    await message.answer(
        "🌙 **Вечірній протокол (5/7)**\n\n"
        "Яка емоція переважала сьогодні?\n\n"
        "(Обери головний емоційний тон дня)",
        reply_markup=dominant_emotion_kb(),
        parse_mode="Markdown",
    )


# -------------------------------------------------------------
# Крок 5. Домінуюча емоція дня -> Крок 6 або Крок 7
# -------------------------------------------------------------
@router.callback_query(EveningCheckin.dominant_emotion, F.data.startswith("emo:"))
async def process_dominant_emotion(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "custom":
        await state.set_state(EveningCheckin.dominant_emotion_custom)
        await callback.message.edit_text("✍️ Напиши головну емоцію сьогодні:", parse_mode="Markdown")
        await callback.answer()
        return

    if val == "skip":
        await state.update_data(dominant_emotion=None, emotion_custom_text=None, emotion_intensity=None)
        await state.set_state(EveningCheckin.cognitive_closure)
        await callback.message.edit_text(
            "🌙 **Вечірній протокол (7/7)**\n\n"
            "За що ти сьогодні можеш собі щиро подякувати або за що відчуваєш вдячність?",
            reply_markup=evening_gratitude_kb(),
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    emo_label = EMOTION_MAP.get(val, val)
    await state.update_data(dominant_emotion=emo_label, emotion_custom_text=None)
    await state.set_state(EveningCheckin.emotion_intensity)

    await callback.message.edit_text(
        f"✅ Емоція: **{emo_label}**\n\n"
        "🌙 **Вечірній протокол (6/7)**\n"
        "Яка інтенсивність цієї емоції?\n\n"
        "(1 — фонова / ледь помітна 🔹 ... 5 — пікова / переповнює 💥)",
        reply_markup=emotion_intensity_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(EveningCheckin.dominant_emotion_custom, ~F.text.startswith("/"))
async def process_emotion_custom(message: Message, state: FSMContext):
    text = message.text.strip()
    await state.update_data(dominant_emotion="Власна емоція", emotion_custom_text=text)
    await state.set_state(EveningCheckin.emotion_intensity)

    await message.answer(
        f"✅ Емоція: **{text}**\n\n"
        "🌙 **Вечірній протокол (6/7)**\n"
        "Яка інтенсивність цієї емоції?\n\n"
        "(1 — фонова / ледь помітна 🔹 ... 5 — пікова / переповнює 💥)",
        reply_markup=emotion_intensity_kb(),
        parse_mode="Markdown",
    )


# -------------------------------------------------------------
# Крок 6. Інтенсивність емоції -> Крок 7: Вдячність / Самоспівчуття
# -------------------------------------------------------------
@router.callback_query(EveningCheckin.emotion_intensity, F.data.startswith("emo_int:"))
async def process_emotion_intensity(callback: CallbackQuery, state: FSMContext):
    intensity = int(callback.data.split(":")[1])
    await state.update_data(emotion_intensity=intensity)
    await state.set_state(EveningCheckin.cognitive_closure)

    await callback.message.edit_text(
        "🌙 **Вечірній протокол (7/7)**\n\n"
        "За що ти сьогодні можеш собі щиро подякувати або за що відчуваєш вдячність?",
        reply_markup=evening_gratitude_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# -------------------------------------------------------------
# Крок 7. Вдячність і збереження фіналу
# -------------------------------------------------------------
@router.callback_query(EveningCheckin.cognitive_closure, F.data.startswith("closure:"))
async def process_gratitude_select(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "custom":
        await state.set_state(EveningCheckin.cognitive_closure_custom)
        await callback.message.edit_text("✍️ За що сьогодні хочеш подякувати собі або світу?", parse_mode="Markdown")
        await callback.answer()
        return

    label = None if val == "skip" else GRATITUDE_MAP.get(val, val)
    await complete_evening_checkin(callback, state, closure_label=label, closure_custom=None)


@router.message(EveningCheckin.cognitive_closure_custom, ~F.text.startswith("/"))
async def process_gratitude_custom(message: Message, state: FSMContext):
    text = message.text.strip()
    await complete_evening_checkin(message, state, closure_label="Своя подяка", closure_custom=text)


async def complete_evening_checkin(
    target,
    state: FSMContext,
    closure_label: Optional[str] = None,
    closure_custom: Optional[str] = None,
):
    data = await state.get_data()
    user_id = target.from_user.id
    today = date.today()

    domains = data.get("selected_domains", [])
    domain_names = [DOMAIN_LABEL_MAP.get(k, k) for k in domains]
    if data.get("custom_activity_text"):
        domain_names.append(data.get("custom_activity_text"))

    try:
        async with async_session() as session:
            await save_evening_checkin(
                session=session,
                telegram_user_id=user_id,
                checkin_date=today,
                activity_domains=domains,
                custom_activity_text=data.get("custom_activity_text"),
                evening_mood=data.get("evening_mood", 3),
                action_result=data.get("action_result"),
                social_state=data.get("social_state"),
                social_custom_text=data.get("social_custom_text"),
                dominant_emotion=data.get("dominant_emotion"),
                emotion_custom_text=data.get("emotion_custom_text"),
                emotion_intensity=data.get("emotion_intensity"),
                cognitive_closure=closure_label,
                closure_custom_text=closure_custom,
                raw_payload=data,
            )
    except Exception as e:
        print("Save evening checkin error:", e)

    await state.clear()

    domains_str = ", ".join(domain_names) if domain_names else "—"
    raw_action_res = data.get("action_result")
    action_res_str = ACTION_RESULT_LABEL_MAP.get(raw_action_res, raw_action_res or "—")
    emo_disp = data.get("emotion_custom_text") or data.get("dominant_emotion") or "—"
    intensity_disp = f" ({data.get('emotion_intensity')}/5)" if data.get("emotion_intensity") else ""
    gratitude_disp = closure_custom or closure_label or "—"

    summary_text = (
        "🌙 **Вечірній протокол збережено!**\n\n"
        f"• Настрій дня: **{data.get('evening_mood')}/5**\n"
        f"• Сфери активності: **{domains_str}**\n"
        f"• Результат дії: **{action_res_str}**\n"
        f"• Соціальний баланс: **{data.get('social_custom_text') or data.get('social_state') or '—'}**\n"
        f"• Емоція: **{emo_disp}{intensity_disp}**\n"
        f"• Вдячність / Підтримка: **{gratitude_disp}**\n\n"
        "День зафіксовано. Дякую за рефлексію! Відпочивай та відновлюйся. 😴"
    )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(summary_text, parse_mode="Markdown")
        await target.answer()
    else:
        await target.answer(summary_text, parse_mode="Markdown")


# -------------------------------------------------------------
# Обробник універсального повернення «« Назад» на 1 крок
# -------------------------------------------------------------
@router.callback_query(F.data.startswith("e_back:"))
async def process_evening_back(callback: CallbackQuery, state: FSMContext):
    target_step = callback.data.split(":")[1]
    data = await state.get_data()

    if target_step == "1":
        await state.set_state(EveningCheckin.activity_domains)
        selected = data.get("selected_domains", [])
        has_custom = bool(data.get("custom_activity_text"))
        await callback.message.edit_text(
            "🌙 **Вечірній протокол (1/7)**\n\n"
            "Куди сьогодні пішов час та енергія?\n\n"
            "(Обери категорії, які займали відчутну частину дня)",
            reply_markup=activity_domains_kb(selected_keys=selected, has_custom=has_custom),
            parse_mode="Markdown",
        )

    elif target_step == "2":
        await state.set_state(EveningCheckin.evening_mood)
        await callback.message.edit_text(
            "🌙 **Вечірній протокол (2/7)**\n\n"
            "Який загальний настрій дня?\n\n"
            "(1 — негативний / важкий 📉\n 5 — позитивний / піднесений 🚀)",
            reply_markup=evening_mood_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "3":
        anchor = data.get("morning_anchor")
        if not anchor or "без плану" in anchor.lower() or "no_plan" in anchor.lower() or data.get("action_result") == "NO_PLAN_SET":
            await state.set_state(EveningCheckin.evening_mood)
            await callback.message.edit_text(
                "🌙 **Вечірній протокол (2/7)**\n\n"
                "Який загальний настрій дня?\n\n"
                "(1 — негативний / важкий 📉\n 5 — позитивний / піднесений 🚀)",
                reply_markup=evening_mood_kb(),
                parse_mode="Markdown",
            )
        else:
            await state.set_state(EveningCheckin.action_result)
            await callback.message.edit_text(
                "🌙 **Вечірній протокол (3/7)**\n\n"
                "Чи вдалося реалізувати заплановану дію?\n\n"
                f"🎯 Твій якір: **«{anchor}»**",
                reply_markup=action_result_kb(),
                parse_mode="Markdown",
            )

    elif target_step == "4":
        await state.set_state(EveningCheckin.social_state)
        await callback.message.edit_text(
            "🌙 **Вечірній протокол (4/7)**\n\n"
            "Як сьогодні контакт із людьми вплинув на твої сили?",
            reply_markup=social_state_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "5":
        await state.set_state(EveningCheckin.dominant_emotion)
        await callback.message.edit_text(
            "🌙 **Вечірній протокол (5/7)**\n\n"
            "Яка емоція переважала сьогодні?\n\n"
            "(Обери головний емоційний тон дня)",
            reply_markup=dominant_emotion_kb(),
            parse_mode="Markdown",
        )

    elif target_step == "6":
        await state.set_state(EveningCheckin.emotion_intensity)
        disp_emo = data.get("emotion_custom_text") or data.get("dominant_emotion") or "Обрана емоція"
        await callback.message.edit_text(
            f"✅ Емоція: **{disp_emo}**\n\n"
            "🌙 **Вечірній протокол (6/7)**\n"
            "Яка інтенсивність цієї емоції?\n\n"
            "(1 — фонова / ледь помітна 🔹 ... 5 — пікова / переповнює 💥)",
            reply_markup=emotion_intensity_kb(),
            parse_mode="Markdown",
        )

    await callback.answer()