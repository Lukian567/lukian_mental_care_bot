from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from bot.config import settings
from bot.content import stubs
from bot.db.base import async_session
from bot.db.repository import (
    get_weekly_stats,
    delete_user_checkins,
    register_or_update_user,
    export_all_checkins_csv,
    export_users_csv,
    get_user_timezone,
    update_user_timezone,
)
from bot.keyboards.checkin_kb import (
    main_menu_kb,
    timezone_kb,
    sleep_duration_kb,
    evening_fact_kb,
    help_kb,
)
from bot.states.checkin_states import MorningCheckin, EveningCheckin, ResetData

router = Router()


def format_stats_text(stats: dict) -> str:
    """Генерує текстове повідомлення на основі агрегованих даних з БД та стріків."""
    current_streak = stats.get("current_streak", 0)
    max_streak = stats.get("max_streak", 0)
    streak_line = f"🔥 **Поточний стрік:** {current_streak} дн. (рекорд: {max_streak} дн.)"

    if stats["morning_count"] == 0 and stats["evening_count"] == 0:
        return (
            "📊 **Статистика за останні 7 днів порожня.**\n\n"
            f"{streak_line}\n\n"
            "Заповнюй ранкові та вечірні чекіни, щоб тут з'явилися показники!"
        )

    m_sleep = f"{stats['avg_sleep_hours']} год" if stats["avg_sleep_hours"] is not None else "—"
    m_sleep_q = f"{stats['avg_sleep_quality']}/5" if stats["avg_sleep_quality"] is not None else "—"
    m_mood = f"{stats['avg_morning_mood']}/5" if stats["avg_morning_mood"] is not None else "—"
    m_anxiety = f"{stats['avg_anxiety']}/5" if stats["avg_anxiety"] is not None else "—"
    m_res = f"{stats['avg_resistance']}/5" if stats["avg_resistance"] is not None else "—"

    e_mood = f"{stats['avg_evening_mood']}/5" if stats["avg_evening_mood"] is not None else "—"
    top_emo = stats.get("top_emotion") or "—"

    return (
        f"📊 **Твій підсумок за останні {stats['days']} днів:**\n\n"
        f"{streak_line}\n\n"
        f"🌅 **Ранок (записів: {stats['morning_count']}):**\n"
        f"• Середній сон: {m_sleep} (якість: {m_sleep_q})\n"
        f"• Настрій після сну: {m_mood}\n"
        f"• Рівень тривоги: {m_anxiety}\n"
        f"• Рівень опору: {m_res}\n\n"
        f"🌙 **Вечір (записів: {stats['evening_count']}):**\n"
        f"• Загальний настрій: {e_mood}\n"
        f"• Домінуюча емоція: {top_emo}"
    )


# ---------------------------------------------------------
# Головне меню та скасування
# ---------------------------------------------------------
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    async with async_session() as session:
        await register_or_update_user(
            session=session,
            telegram_user_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
        )

    is_admin = int(message.from_user.id) == int(settings.admin_user_id)

    text = (
        "👋 Привіт! Я твій щоденник ментального трекінгу.\n\n"
        "Я допомагаю відслідковувати твій стан, якість сну, рівень стресу "
        "та помічати когнітивні паттерни за принципами КПТ.\n\n"
        "Обирай дію нижче або скористайся командами в меню:"
    )
    await message.answer(text, reply_markup=main_menu_kb(is_admin=is_admin))


@router.callback_query(F.data == "back_to_menu")
async def btn_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    is_admin = int(callback.from_user.id) == int(settings.admin_user_id)
    text = (
        "👋 Головне меню щоденника.\n\n"
        "Обирай дію нижче:"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_kb(is_admin=is_admin))
    await callback.answer()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Ніякого активного опитування зараз немає.")
        return

    await state.clear()
    await message.answer("❌ Опитування скасовано. Поточний стан очищено.")


# ---------------------------------------------------------
# Налаштування часового поясу (PL / UA)
# ---------------------------------------------------------
@router.callback_query(F.data == "choose_timezone")
async def btn_choose_timezone(callback: CallbackQuery):
    async with async_session() as session:
        current_tz = await get_user_timezone(session, callback.from_user.id)

    text = (
        "⚙️ **Налаштування часового поясу:**\n\n"
        "Обери країну, за часом якої тобі мають приходити ранкові (08:00) "
        "та вечірні (22:00) нагадування:"
    )
    await callback.message.edit_text(
        text,
        reply_markup=timezone_kb(current_tz=current_tz),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("set_tz:"))
async def process_set_timezone(callback: CallbackQuery):
    new_tz = callback.data.split(":")[1]

    async with async_session() as session:
        await update_user_timezone(session, callback.from_user.id, new_tz)

    tz_name = "🇺🇦 Україна (Київ)" if new_tz == "Europe/Kyiv" else "🇵🇱 Польща (Варшава)"
    await callback.answer(f"Збережено: {tz_name}!", show_alert=True)

    text = (
        f"⚙️ **Часовий пояс оновлено на {tz_name}!**\n\n"
        "Нагадування приходитимуть о 08:00 та 22:00 за цим часом."
    )
    await callback.message.edit_text(
        text,
        reply_markup=timezone_kb(current_tz=new_tz),
        parse_mode="Markdown",
    )


# ---------------------------------------------------------
# Запуск чекінів через кнопки головного меню
# ---------------------------------------------------------
@router.callback_query(F.data == "start_morning")
async def btn_start_morning(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(MorningCheckin.sleep_duration)

    morning_text = getattr(
        stubs,
        "Q_MORNING_SLEEP_DURATION",
        getattr(stubs, "Q_SLEEP_DURATION", "Скільки годин ти спав(-ла)?"),
    )
    await callback.message.answer(morning_text, reply_markup=sleep_duration_kb())
    await callback.answer()


@router.callback_query(F.data == "start_evening")
async def btn_start_evening(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(EveningCheckin.day_fact)

    evening_text = getattr(
        stubs,
        "Q_EVENING_DAY_FACT",
        getattr(stubs, "Q_DAY_FACT", "Головний факт дня: що сьогодні відбулося?"),
    )
    await callback.message.answer(evening_text, reply_markup=evening_fact_kb())
    await callback.answer()


# ---------------------------------------------------------
# Статистика та стріки
# ---------------------------------------------------------
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    async with async_session() as session:
        stats = await get_weekly_stats(session, message.from_user.id, days=7)
    await message.answer(format_stats_text(stats), parse_mode="Markdown")


@router.callback_query(F.data == "show_stats")
async def btn_show_stats(callback: CallbackQuery):
    async with async_session() as session:
        stats = await get_weekly_stats(session, callback.from_user.id, days=7)
    await callback.message.answer(format_stats_text(stats), parse_mode="Markdown")
    await callback.answer()


# ---------------------------------------------------------
# Довідка та безпечне видалення
# ---------------------------------------------------------
@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "ℹ️ **Довідка по щоденнику:**\n\n"
        "• /morning — ранковий чекін (сон, стан, тривога, намір)\n"
        "• /evening — вечірній чекін (підсумок, настрій, емоції)\n"
        "• /stats — статистика за останні 7 днів та стріки\n"
        "• /cancel — перервати поточне активне опитування та скинути стан\n"
        "• /help — ця довідка\n\n"
        "Якщо потрібно повністю скинути всі збережені записи, скористайся кнопкою нижче:"
    )
    await message.answer(text, reply_markup=help_kb(), parse_mode="Markdown")


@router.callback_query(F.data == "request_reset")
async def ask_reset_word(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ResetData.confirm)
    await callback.message.answer(
        "⚠️ **Увага! Ця дія незворотна.**\n\n"
        "Усі твої ранкові та вечірні записи буде назавжди видалено з бази даних.\n\n"
        "Щоб підтвердити видалення, надішли повідомленням слово **ВИДАЛИТИ**.\n"
        "Якщо передумав — надішли команду /cancel або будь-яке інше слово.",
        parse_mode="Markdown",
    )
    await callback.answer()


@router.message(ResetData.confirm)
async def process_reset_confirmation(message: Message, state: FSMContext):
    user_input = message.text.strip()

    if user_input == "ВИДАЛИТИ":
        async with async_session() as session:
            count = await delete_user_checkins(session, message.from_user.id)
        await state.clear()
        await message.answer(
            f"🗑️ **Твою історію повністю очищено.**\n"
            f"Видалено записів: {count}.\n"
            "Можна починати трекінг з чистого аркуша!"
        )
    else:
        await state.clear()
        await message.answer("👌 **Скидання скасовано.** Твої записи збережено в безпеці.")


# ---------------------------------------------------------
# Адміністративний експорт CSV
# ---------------------------------------------------------
async def send_csv_export(target, user_id: int):
    """Формує та надсилає два CSV-файли з бази даних."""
    if int(user_id) != int(settings.admin_user_id):
        if isinstance(target, CallbackQuery):
            await target.answer("⛔ Доступ заборонено.", show_alert=True)
        else:
            await target.answer("⛔ Ця команда доступна лише адміністратору.")
        return

    msg = target.message if isinstance(target, CallbackQuery) else target
    await msg.answer("⏳ Формую повний CSV-експорт обох таблиць...")

    async with async_session() as session:
        checkins_csv = await export_all_checkins_csv(session)
        users_csv = await export_users_csv(session)

    # 1. Таблиця чекінів
    doc_checkins = BufferedInputFile(
        checkins_csv.encode("utf-8"),
        filename="daily_checkins.csv",
    )
    await msg.answer_document(
        document=doc_checkins,
        caption="📊 Таблиця чекінів: `daily_checkins.csv`",
    )

    # 2. Таблиця користувачів
    doc_users = BufferedInputFile(
        users_csv.encode("utf-8"),
        filename="users.csv",
    )
    await msg.answer_document(
        document=doc_users,
        caption="👥 Таблиця користувачів: `users.csv`",
    )

    if isinstance(target, CallbackQuery):
        await target.answer()


@router.message(Command("export"))
async def cmd_export_admin(message: Message):
    await send_csv_export(message, message.from_user.id)


@router.callback_query(F.data == "admin_export")
async def btn_admin_export(callback: CallbackQuery):
    await send_csv_export(callback, callback.from_user.id)