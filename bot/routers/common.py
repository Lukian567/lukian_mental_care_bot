import re
from datetime import date
from typing import Union, Optional
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import settings
from bot.db.base import async_session
from bot.db.repository import (
    register_or_update_user,
    get_user,
    get_user_timezone,
    update_user_timezone,
    update_user_schedule,
    get_weekly_stats,
    delete_user_checkins,
    export_all_checkins_csv,
    export_users_csv,
    export_user_checkins_csv,
)
from bot.keyboards.checkin_kb import (
    main_menu_kb,
    timezone_kb,
    help_kb,
    sleep_hours_kb,
    activity_domains_kb,
    onboarding_tz_kb,
    morning_reminder_time_kb,
    evening_reminder_time_kb,
    schedule_settings_kb,
)
from bot.states.checkin_states import (
    MorningCheckin,
    EveningCheckin,
    ResetData,
    Onboarding,
)

router = Router()


def is_admin_user(user_id: int) -> bool:
    """Чи є користувач власником бота (ADMIN_USER_ID у .env)."""
    return user_id == settings.admin_user_id


def parse_and_validate_time(time_str: str) -> Optional[str]:
    """Перевіряє та нормалізує час у формат HH:MM (наприклад, '8:15' -> '08:15')."""
    match = re.match(r"^([01]?\d|2[0-3]):([0-5]\d)$", time_str.strip())
    if not match:
        return None
    h, m = int(match.group(1)), int(match.group(2))
    return f"{h:02d}:{m:02d}"


async def format_stats_message(user_id: int) -> str:
    """Форматування структурованої та наочної аналітики стану."""
    try:
        async with async_session() as session:
            stats = await get_weekly_stats(session, user_id, days=7)
    except Exception as e:
        print("Stats calculation error:", e)
        return "⚠️ Не вдалося завантажити статистику. Заповни свій перший чекін і спробуй знову."

    c_streak = stats["current_streak"]
    m_streak = stats["max_streak"]
    m_cnt = stats["morning_count"]
    e_cnt = stats["evening_count"]
    total_all = stats.get("total_all_time", 0)

    sleep_str = f"{stats['avg_sleep_hours']} год" if stats["avg_sleep_hours"] is not None else "—"
    sleep_q = f"{stats['avg_sleep_quality']}/5" if stats["avg_sleep_quality"] is not None else "—"
    m_mood = f"{stats['avg_morning_mood']}/5" if stats["avg_morning_mood"] is not None else "—"
    res = f"{stats['avg_resistance']}/5" if stats["avg_resistance"] is not None else "—"
    anx = f"{stats['avg_anxiety']}/5" if stats["avg_anxiety"] is not None else "—"
    e_mood = f"{stats['avg_evening_mood']}/5" if stats["avg_evening_mood"] is not None else "—"
    
    delta_val = stats.get("avg_mood_delta")
    if delta_val is not None:
        sign = "+" if delta_val > 0 else ""
        icon = "📈" if delta_val > 0 else ("📉" if delta_val < 0 else "⚖️")
        delta_str = f"{sign}{delta_val} {icon}"
    else:
        delta_str = "—"

    top_emo = stats.get("top_emotion") or "—"
    top_domains = stats.get("top_domains")
    domains_str = ", ".join(top_domains) if top_domains else "—"
    
    soc_up = stats.get("social_charged", 0)
    soc_down = stats.get("social_drained", 0)

    return (
        "📊 **Аналітика та динаміка твого стану**\n\n"
        "🗓 **Дисципліна трекінгу:**\n"
        f"• Стрік зараз: **{c_streak} дн.** 🔥 (рекорд: {m_streak} дн.)\n"
        f"• Останні 7 днів: 🌅 {m_cnt} ранків | 🌙 {e_cnt} вечорів\n"
        f"• Всього записів за весь час: **{total_all}** чекінів\n\n"
        "🧠 **Ментальний фон (за 7 днів):**\n"
        f"• Настрій: ранок **{m_mood}** ➔ вечір **{e_mood}**\n"
        f"• Динаміка дня (Δ Настрою): **{delta_str}**\n"
        f"• Рівень опору (прокрастинація): **{res}**\n"
        f"• Рівень фонової тривожності: **{anx}**\n"
        f"• Домінуюча емоція: **{top_emo}**\n\n"
        "⚡ **Ресурс та активність:**\n"
        f"• Сон: **{sleep_str}** (якість: {sleep_q})\n"
        f"• Соціальний баланс: 🔋 +{soc_up} сил / 🪫 -{soc_down} виснаження\n"
        f"• Основні сфери: **{domains_str}**\n\n"
        "💡 _Чим регулярніші записи, тим точніші щотижневі патерни._"
    )

# ---------------------------------------------------------
# Команда /start (Автоматичний онбординг для новачків)
# ---------------------------------------------------------
@router.message(CommandStart())
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = None
    try:
        async with async_session() as session:
            user = await register_or_update_user(
                session=session,
                telegram_user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
            )
    except Exception as e:
        print("Register user error:", e)

    # Якщо користувач новий і ще не пройшов онбординг
    if user and not getattr(user, "is_onboarded", True):
        await state.set_state(Onboarding.timezone)
        name = message.from_user.first_name or "друже"
        await message.answer(
            f"Привіт, **{name}**! 👋\n\n"
            "Це щоденник когнітивного стану та щоденної рефлексії.\n"
            "Щоб нагадування приходили вчасно і не турбували посеред ночі, налаштуймо твій графік.\n\n"
            "**Крок 1/3: Обери свій часовий пояс**",
            reply_markup=onboarding_tz_kb(),
            parse_mode="Markdown",
        )
        return

    is_admin = is_admin_user(message.from_user.id)
    await message.answer(
        f"Привіт, **{message.from_user.first_name or 'друже'}**! 👋\n\n"
        "Щоденник когнітивного стану готовий до роботи.\n"
        "Фіксуй ранок, підсумовуй вечір і відстежуй закономірності.",
        reply_markup=main_menu_kb(is_admin=is_admin),
        parse_mode="Markdown",
    )


# ---------------------------------------------------------
# ОНБОРДИНГ: Крок 1 (Таймзона) -> Крок 2 (Ранковий час)
# ---------------------------------------------------------
@router.callback_query(Onboarding.timezone, F.data.startswith("onb_tz:"))
async def process_onboarding_tz(callback: CallbackQuery, state: FSMContext):
    tz = callback.data.split(":")[1]
    await state.update_data(onb_tz=tz)
    await state.set_state(Onboarding.morning_time)

    flag = "🇵🇱" if tz == "Europe/Warsaw" else "🇺🇦"
    city = "Варшава" if tz == "Europe/Warsaw" else "Київ"

    await callback.message.edit_text(
        f"✅ Часовий пояс: **{flag} {city}**\n\n"
        "**Крок 2/3: Ранковий протокол**\n"
        "О котрій годині тобі зручно фіксувати стан і ставити якір дня?",
        reply_markup=morning_reminder_time_kb(show_back=True),
        parse_mode="Markdown",
    )
    await callback.answer()


# ---------------------------------------------------------
# ОНБОРДИНГ ТА НАЛАШТУВАННЯ: Ранковий час
# ---------------------------------------------------------
@router.callback_query(Onboarding.morning_time, F.data.startswith("m_time:"))
async def process_morning_time_select(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "custom":
        await state.set_state(Onboarding.morning_time_custom)
        await callback.message.edit_text(
            "✍️ Введи бажаний ранковий час у форматі `HH:MM` (наприклад, `07:45` або `8:15`):",
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    await proceed_after_morning_time(callback, state, val)
    await callback.answer()


@router.message(Onboarding.morning_time_custom, ~F.text.startswith("/"))
async def process_morning_time_custom(message: Message, state: FSMContext):
    clean_time = parse_and_validate_time(message.text)
    if not clean_time:
        await message.answer("⚠️ Невірний формат. Введи час у форматі `HH:MM` (від `00:00` до `23:59`, наприклад: `07:30`):")
        return

    await proceed_after_morning_time(message, state, clean_time)


async def proceed_after_morning_time(target, state: FSMContext, m_time: str):
    data = await state.get_data()

    if data.get("editing_single_field") == "morning":
        user_id = target.from_user.id
        async with async_session() as session:
            await update_user_schedule(session, user_id, morning_time=m_time)
        await state.clear()
        text = f"✅ Час ранкового нагадування оновлено: **{m_time}**."
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=schedule_settings_kb(), parse_mode="Markdown")
        else:
            await target.answer(text, reply_markup=schedule_settings_kb(), parse_mode="Markdown")
        return

    await state.update_data(onb_morning_time=m_time)
    await state.set_state(Onboarding.evening_time)

    text = (
        f"✅ Ранковий чекін: **{m_time}**\n\n"
        "**Крок 3/3: Вечірній протокол**\n"
        "О котрій годині зазвичай завершуєш справи й готовий підбити підсумки перед сном?"
    )
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=evening_reminder_time_kb(show_back=True), parse_mode="Markdown")
    else:
        await target.answer(text, reply_markup=evening_reminder_time_kb(show_back=True), parse_mode="Markdown")


# ---------------------------------------------------------
# ОНБОРДИНГ ТА НАЛАШТУВАННЯ: Вечірній час + Завершення
# ---------------------------------------------------------
@router.callback_query(Onboarding.evening_time, F.data.startswith("e_time:"))
async def process_evening_time_select(callback: CallbackQuery, state: FSMContext):
    val = callback.data.split(":")[1]

    if val == "custom":
        await state.set_state(Onboarding.evening_time_custom)
        await callback.message.edit_text(
            "✍️ Введи бажаний вечірній час у форматі `HH:MM` (наприклад, `22:15` або `23:00`):",
            parse_mode="Markdown",
        )
        await callback.answer()
        return

    await finish_onboarding_or_edit(callback, state, val)
    await callback.answer()


@router.message(Onboarding.evening_time_custom, ~F.text.startswith("/"))
async def process_evening_time_custom(message: Message, state: FSMContext):
    clean_time = parse_and_validate_time(message.text)
    if not clean_time:
        await message.answer("⚠️ Невірний формат. Введи час у форматі `HH:MM` (від `00:00` до `23:59`, наприклад: `22:30`):")
        return

    await finish_onboarding_or_edit(message, state, clean_time)


async def finish_onboarding_or_edit(target, state: FSMContext, e_time: str):
    data = await state.get_data()
    user_id = target.from_user.id

    if data.get("editing_single_field") == "evening":
        async with async_session() as session:
            await update_user_schedule(session, user_id, evening_time=e_time)
        await state.clear()
        text = f"✅ Час вечірнього нагадування оновлено: **{e_time}**."
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text, reply_markup=schedule_settings_kb(), parse_mode="Markdown")
        else:
            await target.answer(text, reply_markup=schedule_settings_kb(), parse_mode="Markdown")
        return

    tz = data.get("onb_tz", "Europe/Warsaw")
    m_time = data.get("onb_morning_time", "08:00")

    async with async_session() as session:
        await update_user_schedule(
            session=session,
            telegram_user_id=user_id,
            timezone=tz,
            morning_time=m_time,
            evening_time=e_time,
            is_onboarded=True,
        )

    await state.clear()
    is_admin = is_admin_user(user_id)

    flag = "🇵🇱" if tz == "Europe/Warsaw" else "🇺🇦"
    city = "Варшава" if tz == "Europe/Warsaw" else "Київ"

    summary_text = (
        "🎉 **Налаштування збережено!**\n\n"
        f"• Часовий пояс: **{flag} {city}** (`{tz}`)\n"
        f"• 🌅 Ранковий чекін: **{m_time}**\n"
        f"• 🌙 Вечірній чекін: **{e_time}**\n\n"
        "_(Змінити розклад або таймзону можна будь-коли через меню)_\n\n"
        "Головне меню:"
    )

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(summary_text, reply_markup=main_menu_kb(is_admin=is_admin), parse_mode="Markdown")
    else:
        await target.answer(summary_text, reply_markup=main_menu_kb(is_admin=is_admin), parse_mode="Markdown")


# ---------------------------------------------------------
# Навігація «« Назад» в онбордингу
# ---------------------------------------------------------
@router.callback_query(F.data.startswith("onb_back:"))
async def process_onboarding_back(callback: CallbackQuery, state: FSMContext):
    target_step = callback.data.split(":")[1]

    if target_step == "tz":
        await state.set_state(Onboarding.timezone)
        await callback.message.edit_text(
            "**Крок 1/3: Обери свій часовий пояс**",
            reply_markup=onboarding_tz_kb(),
            parse_mode="Markdown",
        )
    elif target_step == "m_time":
        await state.set_state(Onboarding.morning_time)
        data = await state.get_data()
        tz = data.get("onb_tz", "Europe/Warsaw")
        flag = "🇵🇱" if tz == "Europe/Warsaw" else "🇺🇦"
        city = "Варшава" if tz == "Europe/Warsaw" else "Київ"
        await callback.message.edit_text(
            f"✅ Часовий пояс: **{flag} {city}**\n\n"
            "**Крок 2/3: Ранковий протокол**\n"
            "О котрій годині тобі зручно фіксувати стан і ставити якір дня?",
            reply_markup=morning_reminder_time_kb(show_back=True),
            parse_mode="Markdown",
        )

    await callback.answer()


# ---------------------------------------------------------
# Керування графіком і таймзоною з Головного Меню
# ---------------------------------------------------------
@router.callback_query(F.data == "settings_schedule")
async def cb_settings_schedule(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        user = await get_user(session, callback.from_user.id)

    tz = getattr(user, "timezone", "Europe/Warsaw") if user else "Europe/Warsaw"
    m_time = getattr(user, "morning_reminder_time", "08:00") if user else "08:00"
    e_time = getattr(user, "evening_reminder_time", "22:00") if user else "22:00"
    flag = "🇵🇱" if tz == "Europe/Warsaw" else "🇺🇦"

    await callback.message.edit_text(
        "⚙️ **Налаштування розкладу нагадувань**\n\n"
        f"• 🌍 Часовий пояс: {flag} `{tz}`\n"
        f"• 🌅 Ранковий час: **{m_time}**\n"
        f"• 🌙 Вечірній час: **{e_time}**\n\n"
        "Обери, що бажаєш налаштувати:",
        reply_markup=schedule_settings_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "change_tz")
async def cb_change_tz(callback: CallbackQuery):
    async with async_session() as session:
        current_tz = await get_user_timezone(session, callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ **Зміна часового поясу**\n\n"
        f"Поточний пояс: `{current_tz}`\n\n"
        "Обери країну:",
        reply_markup=timezone_kb(current_tz),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "change_m_time")
async def cb_change_m_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Onboarding.morning_time)
    await state.update_data(editing_single_field="morning")
    await callback.message.edit_text(
        "🌅 **Зміна часу ранкового чекіну**\n\n"
        "О котрій годині надсилати ранкове сповіщення?",
        reply_markup=morning_reminder_time_kb(show_back=False),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "change_e_time")
async def cb_change_e_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Onboarding.evening_time)
    await state.update_data(editing_single_field="evening")
    await callback.message.edit_text(
        "🌙 **Зміна часу вечірнього чекіну**\n\n"
        "О котрій годині надсилати вечірнє сповіщення?",
        reply_markup=evening_reminder_time_kb(show_back=False),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_tz:"))
async def cb_set_timezone(callback: CallbackQuery):
    new_tz = callback.data.split(":")[1]
    async with async_session() as session:
        await update_user_timezone(session, callback.from_user.id, new_tz)

    city = "Варшава" if new_tz == "Europe/Warsaw" else "Київ"
    flag = "🇵🇱" if new_tz == "Europe/Warsaw" else "🇺🇦"
    await callback.message.edit_text(
        f"✅ Часовий пояс встановлено: **{flag} {city}** (`{new_tz}`).",
        reply_markup=schedule_settings_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ---------------------------------------------------------
# Базові команди /menu, /help, /cancel, /stats
# ---------------------------------------------------------
@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    is_admin = is_admin_user(message.from_user.id)
    await message.answer(
        "Головне меню:",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "ℹ️ **Довідка:**\n\n"
        "• /morning — ранковий чекін\n"
        "• /evening — вечірній чекін\n"
        "• /stats — динаміка за останні 7 днів\n"
        "• /cancel — скинути поточний крок\n\n"
        "Усі дані зберігаються конфіденційно у локальній базі PostgreSQL.",
        reply_markup=help_kb(),
        parse_mode="Markdown",
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    is_admin = is_admin_user(message.from_user.id)
    await message.answer(
        "❌ Скасовано. Повертаємося до головного меню.",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    text = await format_stats_message(message.from_user.id)
    await message.answer(text, parse_mode="Markdown")


# ---------------------------------------------------------
# Запуск чекінів через кнопки головного меню
# ---------------------------------------------------------
@router.callback_query(F.data == "start_morning")
async def btn_start_morning(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(MorningCheckin.sleep_hours)
    await callback.message.answer(
        "🌅 **Ранковий протокол (1/6)**\n\nСкільки тривав сон?",
        reply_markup=sleep_hours_kb(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "start_evening")
async def btn_start_evening(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(EveningCheckin.activity_domains)
    await state.update_data(selected_domains=[], custom_activity_text=None)
    await callback.message.answer(
        "🌙 **Вечірній протокол (1/7)**\n\n"
        "Куди сьогодні пішов основний ресурс і час?\n\n"
        "(Обери один або декілька пунктів, які займали відчутну частину дня)",
        reply_markup=activity_domains_kb(selected_keys=[]),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "show_stats")
async def cb_show_stats(callback: CallbackQuery):
    text = await format_stats_message(callback.from_user.id)
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = is_admin_user(callback.from_user.id)
    await callback.message.edit_text(
        "Головне меню:",
        reply_markup=main_menu_kb(is_admin=is_admin),
    )
    await callback.answer()


# ---------------------------------------------------------
# Експорт даних (ВИКЛЮЧНО ДЛЯ АДМІНІСТРАТОРА)
# ---------------------------------------------------------
@router.callback_query(F.data == "admin_export")
@router.message(Command("export"))
@router.message(Command("admin_export"))
async def cb_admin_export(event: Union[CallbackQuery, Message]):
    user_id = event.from_user.id

    if not is_admin_user(user_id):
        text = "⛔ Доступ заборонено. Експорт бази дозволено лише власнику бота."
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        else:
            await event.answer(text)
        return

    try:
        async with async_session() as session:
            checkins_csv = await export_all_checkins_csv(session)
            users_csv = await export_users_csv(session)

        checkins_file = BufferedInputFile(
            file=checkins_csv.encode("utf-8-sig"),
            filename=f"all_checkins_{date.today().isoformat()}.csv",
        )
        users_file = BufferedInputFile(
            file=users_csv.encode("utf-8-sig"),
            filename=f"users_{date.today().isoformat()}.csv",
        )

        msg = event.message if isinstance(event, CallbackQuery) else event
        await msg.answer_document(checkins_file, caption="📊 Усі чекіни по всіх користувачах (Tableau / BigQuery)")
        await msg.answer_document(users_file, caption="👥 Таблиця всіх користувачів")
    except Exception as e:
        print("Export error:", e)
        error_msg = f"⚠️ Помилка експорту: {e}"
        if isinstance(event, CallbackQuery):
            await event.message.answer(error_msg)
        else:
            await event.answer(error_msg)

    if isinstance(event, CallbackQuery):
        await event.answer()


# ---------------------------------------------------------
# Скидання даних
# ---------------------------------------------------------
@router.callback_query(F.data == "request_reset")
async def cb_request_reset(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ResetData.confirm)
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑 Так, видалити все", callback_data="confirm_reset"),
        InlineKeyboardButton(text="« Скасувати", callback_data="back_to_menu"),
    )
    await callback.message.edit_text(
        "⚠️ **Увага!** Це видалить усі твої попередні записи чекінів та скине стрік.\n\n"
        "Підтверджуєш видалення?",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(ResetData.confirm, F.data == "confirm_reset")
async def cb_confirm_reset(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        count = await delete_user_checkins(session, callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        f"🗑️ Твої записи видалено (очищено: {count} рядків).\n\n"
        "Ти можеш почати новий трекінг у будь-який момент через /menu.",
        parse_mode="Markdown",
    )
    await callback.answer()