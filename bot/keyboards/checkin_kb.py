from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Головне меню: експорт доступний виключно адміністратору."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌅 Ранковий чекін", callback_data="start_morning"),
        InlineKeyboardButton(text="🌙 Вечірній чекін", callback_data="start_evening"),
    )
    if is_admin:
        builder.row(
            InlineKeyboardButton(text="📊 Моя статистика", callback_data="show_stats"),
            InlineKeyboardButton(text="📥 Експорт бази (Admin)", callback_data="admin_export"),
        )
    else:
        builder.row(
            InlineKeyboardButton(text="📊 Моя статистика", callback_data="show_stats"),
        )
    builder.row(
        InlineKeyboardButton(text="⚙️ Графік і таймзона", callback_data="settings_schedule"),
    )
    return builder.as_markup()


def schedule_settings_kb() -> InlineKeyboardMarkup:
    """Меню керування графіком і нагадуваннями."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🌍 Змінити часовий пояс", callback_data="change_tz"),
    )
    builder.row(
        InlineKeyboardButton(text="🌅 Ранковий час", callback_data="change_m_time"),
        InlineKeyboardButton(text="🌙 Вечірній час", callback_data="change_e_time"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад у меню", callback_data="back_to_menu"),
    )
    return builder.as_markup()


def timezone_kb(current_tz: str = "Europe/Warsaw") -> InlineKeyboardMarkup:
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


# -------------------------------------------------------------
# ОНБОРДИНГ ТА НАЛАШТУВАННЯ ЧАСУ
# -------------------------------------------------------------

def onboarding_tz_kb() -> InlineKeyboardMarkup:
    """Вибір часового поясу під час онбордингу."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🇵🇱 Польща (Варшава)", callback_data="onb_tz:Europe/Warsaw"),
    )
    builder.row(
        InlineKeyboardButton(text="🇺🇦 Україна (Київ)", callback_data="onb_tz:Europe/Kyiv"),
    )
    return builder.as_markup()


def morning_reminder_time_kb(show_back: bool = True) -> InlineKeyboardMarkup:
    """Вибір часу для ранкового нагадування."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="07:00", callback_data="m_time:07:00"),
        InlineKeyboardButton(text="07:30", callback_data="m_time:07:30"),
        InlineKeyboardButton(text="08:00", callback_data="m_time:08:00"),
    )
    builder.row(
        InlineKeyboardButton(text="08:30", callback_data="m_time:08:30"),
        InlineKeyboardButton(text="09:00", callback_data="m_time:09:00"),
        InlineKeyboardButton(text="09:30", callback_data="m_time:09:30"),
    )
    builder.row(
        InlineKeyboardButton(text="✍️ Ввести свій час", callback_data="m_time:custom"),
    )
    if show_back:
        builder.row(
            InlineKeyboardButton(text="« Назад", callback_data="onb_back:tz"),
        )
    return builder.as_markup()


def evening_reminder_time_kb(show_back: bool = True) -> InlineKeyboardMarkup:
    """Вибір часу для вечірнього нагадування."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="21:00", callback_data="e_time:21:00"),
        InlineKeyboardButton(text="21:30", callback_data="e_time:21:30"),
        InlineKeyboardButton(text="22:00", callback_data="e_time:22:00"),
    )
    builder.row(
        InlineKeyboardButton(text="22:30", callback_data="e_time:22:30"),
        InlineKeyboardButton(text="23:00", callback_data="e_time:23:00"),
        InlineKeyboardButton(text="23:30", callback_data="e_time:23:30"),
    )
    builder.row(
        InlineKeyboardButton(text="✍️ Ввести свій час", callback_data="e_time:custom"),
    )
    if show_back:
        builder.row(
            InlineKeyboardButton(text="« Назад", callback_data="onb_back:m_time"),
        )
    return builder.as_markup()


# -------------------------------------------------------------
# ЧАСТИНА I. РАНКОВИЙ ПРОТОКОЛ (6 кроків)
# -------------------------------------------------------------

def sleep_hours_kb() -> InlineKeyboardMarkup:
    """Крок 1.1. 5 рівних діапазонів тривалості сну + точний ввід."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="< 6", callback_data="sleep_h:5.5"),
        InlineKeyboardButton(text="6–7", callback_data="sleep_h:6.5"),
        InlineKeyboardButton(text="7–8", callback_data="sleep_h:7.5"),
        InlineKeyboardButton(text="8–9", callback_data="sleep_h:8.5"),
        InlineKeyboardButton(text="> 9", callback_data="sleep_h:9.5"),
    )
    builder.row(
        InlineKeyboardButton(text="✍️ Ввести точний час", callback_data="sleep_h:custom")
    )
    return builder.as_markup()


def sleep_quality_kb() -> InlineKeyboardMarkup:
    """Крок 1.2. Суб'єктивна якість сну."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1 📉", callback_data="sleep_q:1"),
        InlineKeyboardButton(text="2", callback_data="sleep_q:2"),
        InlineKeyboardButton(text="3", callback_data="sleep_q:3"),
        InlineKeyboardButton(text="4", callback_data="sleep_q:4"),
        InlineKeyboardButton(text="5 ⚡", callback_data="sleep_q:5"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="m_back:1")
    )
    return builder.as_markup()


def morning_mood_kb() -> InlineKeyboardMarkup:
    """Крок 2. Ранковий настрій."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1 📉", callback_data="m_mood:1"),
        InlineKeyboardButton(text="2", callback_data="m_mood:2"),
        InlineKeyboardButton(text="3", callback_data="m_mood:3"),
        InlineKeyboardButton(text="4", callback_data="m_mood:4"),
        InlineKeyboardButton(text="5 🚀", callback_data="m_mood:5"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="m_back:2")
    )
    return builder.as_markup()


def morning_resistance_kb() -> InlineKeyboardMarkup:
    """Крок 3. Рівень внутрішнього опору."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1 🟢", callback_data="m_res:1"),
        InlineKeyboardButton(text="2", callback_data="m_res:2"),
        InlineKeyboardButton(text="3", callback_data="m_res:3"),
        InlineKeyboardButton(text="4", callback_data="m_res:4"),
        InlineKeyboardButton(text="5 🛑", callback_data="m_res:5"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="m_back:3")
    )
    return builder.as_markup()


def morning_anxiety_kb() -> InlineKeyboardMarkup:
    """Крок 4. Фонова тривожність."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1 🧘", callback_data="m_anx:1"),
        InlineKeyboardButton(text="2", callback_data="m_anx:2"),
        InlineKeyboardButton(text="3", callback_data="m_anx:3"),
        InlineKeyboardButton(text="4", callback_data="m_anx:4"),
        InlineKeyboardButton(text="5 ⚡", callback_data="m_anx:5"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="m_back:4")
    )
    return builder.as_markup()


def morning_thought_kb() -> InlineKeyboardMarkup:
    """Крок 5. Ранковий когнітивний фокус уваги."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Завдання", callback_data="thought_p:tasks"),
        InlineKeyboardButton(text="⚡ Тривожні очікування", callback_data="thought_p:anxiety"),
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Румінація / вчорашнє", callback_data="thought_p:rumination"),
        InlineKeyboardButton(text="🌫 Ментальний туман", callback_data="thought_p:fog"),
    )
    builder.row(
        InlineKeyboardButton(text="🧘 Спокійна ясна голова", callback_data="thought_p:calm"),
        InlineKeyboardButton(text="🔥 Драйв / очікування", callback_data="thought_p:drive"),
    )
    builder.row(
        InlineKeyboardButton(text="✍️ Написати текстом", callback_data="thought_p:custom"),
        InlineKeyboardButton(text="⏭ Пропустити", callback_data="thought_p:skip"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="m_back:5")
    )
    return builder.as_markup()


def morning_action_kb() -> InlineKeyboardMarkup:
    """Крок 6. Поведінковий якір дня."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎯 Закрити ключову робочу/навчальну задачу", callback_data="anchor:task"))
    builder.row(InlineKeyboardButton(text="👥 Соціальний контакт / зустріч / дзвінок", callback_data="anchor:social"))
    builder.row(InlineKeyboardButton(text="🏋️ Провести тренування / фізичну активність", callback_data="anchor:workout"))
    builder.row(InlineKeyboardButton(text="🚶 Прогулянка / зміна середовища", callback_data="anchor:walk"))
    builder.row(InlineKeyboardButton(text="🧹 Навести лад у просторі", callback_data="anchor:order"))
    builder.row(InlineKeyboardButton(text="🛋 Свідомо відпочити без почуття провини", callback_data="anchor:rest"))
    builder.row(InlineKeyboardButton(text="✍️ Своя конкретна дія (текстом)", callback_data="anchor:custom"))
    builder.row(InlineKeyboardButton(text="⚪ День без плану / спостереження", callback_data="anchor:no_plan"))
    builder.row(InlineKeyboardButton(text="« Назад", callback_data="m_back:6"))
    return builder.as_markup()


# -------------------------------------------------------------
# ЧАСТИНА II. ВЕЧІРНІЙ ПРОТОКОЛ (6 кроків)
# -------------------------------------------------------------

DOMAIN_ITEMS = [
    ("cognitive", "🧠 Когнітивна праця (навчання / робота)"),
    ("physical", "🏃 Фізична активність (тренування / рух)"),
    ("social", "👥 Соціальна взаємодія (зустрічі / спілкування)"),
    ("screen", "📱 Екранний час (скролінг / контент)"),
    ("rest", "🔋 Відновлення (тиша / сон / відпочинок)"),
    ("routine", "🧹 Побут (рутина / порядок)"),
    ("stress", "⚡ Гострі стресори (форс-мажор / тиск)"),
]

def activity_domains_kb(selected_keys: Optional[List[str]] = None, has_custom: bool = False) -> InlineKeyboardMarkup:
    """Крок 1. Сфери навантаження (Мультиселект)."""
    selected_set = set(selected_keys or [])
    builder = InlineKeyboardBuilder()
    for key, label in DOMAIN_ITEMS:
        mark = "✅ " if key in selected_set else ""
        builder.row(InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"dom_tog:{key}"))

    custom_mark = "✅ " if has_custom else ""
    builder.row(InlineKeyboardButton(text=f"{custom_mark}✍️ Інше (вказати текстом)", callback_data="dom_custom"))
    builder.row(InlineKeyboardButton(text="➡️ Зберегти вибір", callback_data="dom_save"))
    return builder.as_markup()


def evening_mood_kb() -> InlineKeyboardMarkup:
    """Крок 2. Загальний настрій дня."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1 📉", callback_data="e_mood:1"),
        InlineKeyboardButton(text="2", callback_data="e_mood:2"),
        InlineKeyboardButton(text="3", callback_data="e_mood:3"),
        InlineKeyboardButton(text="4", callback_data="e_mood:4"),
        InlineKeyboardButton(text="5 🚀", callback_data="e_mood:5"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="e_back:1")
    )
    return builder.as_markup()


def action_result_kb() -> InlineKeyboardMarkup:
    """Крок 3. Верифікація ранкового наміру."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Так, повністю", callback_data="act_res:DONE"))
    builder.row(InlineKeyboardButton(text="⏳ Частково", callback_data="act_res:PARTIAL"))
    builder.row(InlineKeyboardButton(text="❌ Ні, не зробив(-ла)", callback_data="act_res:MISSED"))
    builder.row(InlineKeyboardButton(text="🔄 Завадили обставини", callback_data="act_res:OBSTACLES"))
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="e_back:2")
    )
    return builder.as_markup()


def social_state_kb() -> InlineKeyboardMarkup:
    """Крок 4. Соціальний енергетичний баланс."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔋 Додало сил / підняло настрій", callback_data="soc:charge"))
    builder.row(InlineKeyboardButton(text="⚖️ Був серед людей — звичайна рутина", callback_data="soc:routine"))
    builder.row(InlineKeyboardButton(text="🪫 Забрало сили / виснажило", callback_data="soc:drain"))
    builder.row(InlineKeyboardButton(text="👤 Був серед людей, але ніби сам", callback_data="soc:alienation"))
    builder.row(InlineKeyboardButton(text="🧘 Побув наодинці — відновив сили", callback_data="soc:solitude"))
    builder.row(InlineKeyboardButton(text="🏠 Побув наодинці — звична нормальна рутина", callback_data="soc:alone_routine"))
    builder.row(InlineKeyboardButton(text="🚪 Був сам — це пригнітило / брак людей", callback_data="soc:isolation_drained"))
    builder.row(
        InlineKeyboardButton(text="✍️ Написати текстом", callback_data="soc:custom"),
        InlineKeyboardButton(text="⏭ Пропустити", callback_data="soc:skip"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="e_back:3")
    )
    return builder.as_markup()


def dominant_emotion_kb() -> InlineKeyboardMarkup:
    """Крок 5. Домінуюча емоція дня."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔥 Драйв / Радість", callback_data="emo:drive_joy"),
        InlineKeyboardButton(text="😌 Спокій / Баланс", callback_data="emo:calm_balance"),
    )
    builder.row(
        InlineKeyboardButton(text="⚡ Тривога / Напруга", callback_data="emo:anxiety_tension"),
        InlineKeyboardButton(text="😡 Злість / Дратівливість", callback_data="emo:anger_irritation"),
    )
    builder.row(
        InlineKeyboardButton(text="🌧 Сум / Пригніченість", callback_data="emo:sadness_down"),
        InlineKeyboardButton(text="🪫 Апатія / Порожнеча", callback_data="emo:apathy_empty"),
    )
    builder.row(
        InlineKeyboardButton(text="😔 Провина / Сором", callback_data="emo:guilt_shame"),
        InlineKeyboardButton(text="✍️ Написати текстом", callback_data="emo:custom"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="e_back:4"),
        InlineKeyboardButton(text="⏭ Пропустити", callback_data="emo:skip"),
    )
    return builder.as_markup()


def emotion_intensity_kb() -> InlineKeyboardMarkup:
    """Крок 6. Інтенсивність емоції (фінал вечірнього чекіну)."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="1 🔹", callback_data="emo_int:1"),
        InlineKeyboardButton(text="2", callback_data="emo_int:2"),
        InlineKeyboardButton(text="3", callback_data="emo_int:3"),
        InlineKeyboardButton(text="4", callback_data="emo_int:4"),
        InlineKeyboardButton(text="5 💥", callback_data="emo_int:5"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="e_back:5")
    )
    return builder.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🗑️ Скинути всі мої дані", callback_data="request_reset")
    )
    return builder.as_markup()

def evening_gratitude_kb() -> InlineKeyboardMarkup:
    """Крок 7. Вдячність і підтримка дня."""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🛋 За те, що впорався(-лась) із цим днем", callback_data="closure:coped"))
    builder.row(InlineKeyboardButton(text="🎯 За дисципліну та конкретні зроблені кроки", callback_data="closure:discipline"))
    builder.row(InlineKeyboardButton(text="🔋 За те, що дав(-ла) собі час перепочити", callback_data="closure:rest"))
    builder.row(InlineKeyboardButton(text="🫂 За людей поруч або добрий вчинок", callback_data="closure:social"))
    builder.row(
        InlineKeyboardButton(text="✍️ Написати своє (текстом)", callback_data="closure:custom"),
        InlineKeyboardButton(text="⏭ Пропустити", callback_data="closure:skip"),
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="e_back:6")
    )
    return builder.as_markup()