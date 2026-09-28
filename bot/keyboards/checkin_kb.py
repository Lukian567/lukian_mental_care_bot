from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.content import stubs


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Головне меню бота."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌅 Ранковий чекін", callback_data="start_morning"),
        InlineKeyboardButton(text="🌙 Вечірній чекін", callback_data="start_evening"),
    )
    builder.row(
        InlineKeyboardButton(text="📊 Моя статистика", callback_data="show_stats"),
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Часовий пояс (PL / UA)", callback_data="choose_timezone"),
    )
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="📥 Експорт CSV (Admin)", callback_data="admin_export"),
        )
    return builder.as_markup()


def timezone_kb(current_tz: str = "Europe/Warsaw") -> InlineKeyboardMarkup:
    """Клавіатура швидкого вибору часового поясу."""
    builder = InlineKeyboardBuilder()
    pl_mark = " ✅" if current_tz == "Europe/Warsaw" else ""
    ua_mark = " ✅" if current_tz == "Europe/Kyiv" else ""
    builder.row(
        InlineKeyboardButton(text=f"🇵🇱 Польща (Варшава){pl_mark}", callback_data="set_tz:Europe/Warsaw"),
    )
    builder.row(
        InlineKeyboardButton(text=f"🇺🇦 Україна (Київ){ua_mark}", callback_data="set_tz:Europe/Kyiv"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад у меню", callback_data="back_to_menu"),
    )
    return builder.as_markup()


def scale_kb(prefix: str) -> InlineKeyboardMarkup:
    """Універсальна шкала оцінки від 1 до 5."""
    builder = InlineKeyboardBuilder()
    for i in range(1, 6):
        builder.add(InlineKeyboardButton(text=str(i), callback_data=f"{prefix}:{i}"))
    builder.adjust(5)
    return builder.as_markup()


def sleep_duration_kb() -> InlineKeyboardMarkup:
    """Швидкий вибір тривалості сну."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Менше 4 год", callback_data="sleep_dur:210"))
    builder.row(InlineKeyboardButton(text="4–6 год", callback_data="sleep_dur:300"))
    builder.row(InlineKeyboardButton(text="6–8 год", callback_data="sleep_dur:420"))
    builder.row(InlineKeyboardButton(text="Більше 8 год", callback_data="sleep_dur:540"))
    return builder.as_markup()


def morning_thought_kb() -> InlineKeyboardMarkup:
    """Ранкова автоматична думка."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=stubs.THOUGHT_AGAIN, callback_data="thought:again"))
    builder.row(InlineKeyboardButton(text=stubs.THOUGHT_NOTHING, callback_data="thought:nothing"))
    builder.row(InlineKeyboardButton(text=stubs.THOUGHT_BETTER, callback_data="thought:better"))
    builder.row(InlineKeyboardButton(text=stubs.THOUGHT_TASK, callback_data="thought:task"))
    builder.row(InlineKeyboardButton(text=stubs.THOUGHT_NEUTRAL, callback_data="thought:neutral"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="thought:custom"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="thought:skip"))
    return builder.as_markup()


def morning_action_kb() -> InlineKeyboardMarkup:
    """Ранкова мікро-дія на день."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=stubs.ACTION_SELF_CARE, callback_data="action:self_care"))
    builder.row(InlineKeyboardButton(text=stubs.ACTION_WALK, callback_data="action:walk"))
    builder.row(InlineKeyboardButton(text=stubs.ACTION_STUDY_WORK, callback_data="action:work"))
    builder.row(InlineKeyboardButton(text=stubs.ACTION_SURVIVE, callback_data="action:survive"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="action:custom"))
    builder.row(InlineKeyboardButton(text="⏭️ Без плану", callback_data="action:skip"))
    return builder.as_markup()


def evening_fact_kb() -> InlineKeyboardMarkup:
    """Факт дня."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=stubs.FACT_BED, callback_data="fact:bed"))
    builder.row(InlineKeyboardButton(text=stubs.FACT_BASE, callback_data="fact:base"))
    builder.row(InlineKeyboardButton(text=stubs.FACT_OUT, callback_data="fact:out"))
    builder.row(InlineKeyboardButton(text=stubs.FACT_PRODUCTIVE, callback_data="fact:prod"))
    builder.row(InlineKeyboardButton(text=stubs.FACT_NOTHING, callback_data="fact:nothing"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="fact:custom"))
    return builder.as_markup()


def action_done_kb() -> InlineKeyboardMarkup:
    """Статус виконання мікро-дії."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=stubs.STATUS_DONE, callback_data="done:yes"))
    builder.row(InlineKeyboardButton(text=stubs.STATUS_PARTIAL, callback_data="done:part"))
    builder.row(InlineKeyboardButton(text=stubs.STATUS_FAIL, callback_data="done:no"))
    builder.row(InlineKeyboardButton(text=stubs.STATUS_NO_PLAN, callback_data="done:none"))
    return builder.as_markup()


def contact_quality_kb() -> InlineKeyboardMarkup:
    """Якість соціального контакту."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=stubs.CONTACT_GOOD, callback_data="contact:good"))
    builder.row(InlineKeyboardButton(text=stubs.CONTACT_WORK, callback_data="contact:work"))
    builder.row(InlineKeyboardButton(text=stubs.CONTACT_ALONE_IN_CROWD, callback_data="contact:alone"))
    builder.row(InlineKeyboardButton(text=stubs.CONTACT_AVOIDED, callback_data="contact:avoid"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="contact:custom"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="contact:skip"))
    return builder.as_markup()


def emotion_kb() -> InlineKeyboardMarkup:
    """Переважна емоція дня."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=stubs.EMO_SADNESS, callback_data="emo:sadness"),
        InlineKeyboardButton(text=stubs.EMO_ANXIETY, callback_data="emo:anxiety"),
    )
    builder.row(
        InlineKeyboardButton(text=stubs.EMO_ANGER, callback_data="emo:anger"),
        InlineKeyboardButton(text=stubs.EMO_GUILT, callback_data="emo:guilt"),
    )
    builder.row(
        InlineKeyboardButton(text=stubs.EMO_EMPTINESS, callback_data="emo:emptiness"),
        InlineKeyboardButton(text=stubs.EMO_CALM, callback_data="emo:calm"),
    )
    builder.row(InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="emo:skip"))
    return builder.as_markup()


def compassion_kb() -> InlineKeyboardMarkup:
    """Самопідтримка (self-compassion)."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=stubs.COMPASSION_BEST, callback_data="comp:best"))
    builder.row(InlineKeyboardButton(text=stubs.COMPASSION_NORMAL, callback_data="comp:normal"))
    builder.row(InlineKeyboardButton(text=stubs.COMPASSION_ENOUGH, callback_data="comp:enough"))
    builder.row(InlineKeyboardButton(text=stubs.COMPASSION_TOMORROW, callback_data="comp:tomorrow"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_WRITE_CUSTOM, callback_data="comp:custom"))
    builder.row(InlineKeyboardButton(text=stubs.BTN_SKIP, callback_data="comp:skip"))
    return builder.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    """Кнопка скидання в довідці."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑️ Скинути всі мої дані", callback_data="request_reset")
    )
    return builder.as_markup()