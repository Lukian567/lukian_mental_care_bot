import csv
import io
from collections import Counter
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import CheckinPeriod, DailyCheckin, User


# ==========================================
# 👤 КОРИСТУВАЧІ ТА РОЗКЛАД
# ==========================================

async def register_or_update_user(
    session: AsyncSession,
    telegram_user_id: int,
    first_name: Optional[str] = None,
    username: Optional[str] = None,
) -> User:
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    res = await session.execute(stmt)
    user = res.scalars().first()

    if user:
        user.first_name = first_name
        user.username = username
        user.is_active = True
    else:
        user = User(
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            username=username,
            timezone="Europe/Warsaw",
            morning_reminder_time="08:00",
            evening_reminder_time="22:00",
            is_onboarded=False,
            is_active=True,
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


async def get_user(session: AsyncSession, telegram_user_id: int) -> Optional[User]:
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    res = await session.execute(stmt)
    return res.scalars().first()


async def get_user_timezone(session: AsyncSession, telegram_user_id: int) -> str:
    stmt = select(User.timezone).where(User.telegram_user_id == telegram_user_id)
    res = await session.execute(stmt)
    tz = res.scalars().first()
    return tz or "Europe/Warsaw"


async def update_user_timezone(session: AsyncSession, telegram_user_id: int, timezone: str) -> None:
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    res = await session.execute(stmt)
    user = res.scalars().first()
    if user:
        user.timezone = timezone
        await session.commit()


async def update_user_schedule(
    session: AsyncSession,
    telegram_user_id: int,
    timezone: Optional[str] = None,
    morning_time: Optional[str] = None,
    evening_time: Optional[str] = None,
    is_onboarded: Optional[bool] = None,
) -> None:
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    res = await session.execute(stmt)
    user = res.scalars().first()
    if user:
        if timezone is not None:
            user.timezone = timezone
        if morning_time is not None:
            user.morning_reminder_time = morning_time
        if evening_time is not None:
            user.evening_reminder_time = evening_time
        if is_onboarded is not None:
            user.is_onboarded = is_onboarded
        await session.commit()


async def get_active_users_by_timezone(session: AsyncSession, timezone: str) -> List[User]:
    stmt = select(User).where(User.timezone == timezone, User.is_active == True)
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def get_users_for_reminder(
    session: AsyncSession,
    timezone: str,
    target_time: str,
    period: str,
) -> List[User]:
    time_column = (
        User.morning_reminder_time if period == "morning" else User.evening_reminder_time
    )
    stmt = select(User).where(
        User.timezone == timezone,
        User.is_active == True,
        time_column == target_time,
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


# ==========================================
# 🌅 РАНКОВИЙ ЧЕКІН
# ==========================================

async def save_morning_checkin(
    session: AsyncSession,
    telegram_user_id: int,
    checkin_date: date,
    sleep_hours: float,
    sleep_quality: int,
    morning_mood: int,
    morning_resistance: int,
    morning_anxiety: int,
    morning_thought: Optional[str] = None,
    morning_thought_pattern: Optional[str] = None,
    morning_thought_custom: Optional[str] = None,
    morning_action_anchor: Optional[str] = None,
    raw_payload: Optional[dict] = None,
    **kwargs: Any,
) -> DailyCheckin:
    stmt = (
        select(DailyCheckin)
        .where(
            DailyCheckin.telegram_user_id == telegram_user_id,
            DailyCheckin.checkin_date == checkin_date,
            DailyCheckin.period.in_([CheckinPeriod.morning, "morning"]),
        )
        .order_by(DailyCheckin.id.desc())
    )
    res = await session.execute(stmt)
    checkin = res.scalars().first()

    if not checkin:
        checkin = DailyCheckin(
            telegram_user_id=telegram_user_id,
            checkin_date=checkin_date,
            period=CheckinPeriod.morning,
        )
        session.add(checkin)

    # Визначаємо текст думки без службової заглушки "Думка"
    thought = morning_thought or morning_thought_custom or morning_thought_pattern
    if thought == "Думка":
        thought = morning_thought_custom or None

    checkin.sleep_hours = sleep_hours
    checkin.sleep_quality = sleep_quality
    checkin.morning_mood = morning_mood
    checkin.morning_resistance = morning_resistance
    checkin.morning_anxiety = morning_anxiety
    checkin.morning_thought = thought
    checkin.morning_action_anchor = morning_action_anchor
    checkin.raw_payload = raw_payload

    await session.commit()
    await session.refresh(checkin)
    return checkin


# ==========================================
# 🌙 ВЕЧІРНІЙ ЧЕКІН
# ==========================================

async def save_evening_checkin(
    session: AsyncSession,
    telegram_user_id: int,
    checkin_date: date,
    activity_domains: List[str],
    evening_mood: int = 0,
    action_result: Optional[str] = None,
    social_state: Optional[str] = None,
    social_custom_text: Optional[str] = None,
    dominant_emotion: Optional[str] = None,
    emotion_custom_text: Optional[str] = None,
    emotion_intensity: Optional[int] = None,
    cognitive_closure: Optional[str] = None,
    closure_custom_text: Optional[str] = None,
    raw_payload: Optional[dict] = None,
    **kwargs: Any,
) -> DailyCheckin:
    stmt = (
        select(DailyCheckin)
        .where(
            DailyCheckin.telegram_user_id == telegram_user_id,
            DailyCheckin.checkin_date == checkin_date,
            DailyCheckin.period.in_([CheckinPeriod.evening, "evening"]),
        )
        .order_by(DailyCheckin.id.desc())
    )
    res = await session.execute(stmt)
    checkin = res.scalars().first()

    if not checkin:
        checkin = DailyCheckin(
            telegram_user_id=telegram_user_id,
            checkin_date=checkin_date,
            period=CheckinPeriod.evening,
        )
        session.add(checkin)

    checkin.evening_mood = evening_mood
    checkin.activity_domains = activity_domains
    checkin.action_result = action_result
    checkin.social_state = social_custom_text or social_state
    checkin.dominant_emotion = emotion_custom_text or dominant_emotion
    checkin.emotion_intensity = emotion_intensity
    checkin.cognitive_closure = closure_custom_text or cognitive_closure
    checkin.raw_payload = raw_payload

    await session.commit()
    await session.refresh(checkin)
    return checkin


# ==========================================
# 🔍 ДОПОМІЖНІ ЗАПИТИ ТА СТАТИСТИКА
# ==========================================

async def get_today_morning_anchor(
    session: AsyncSession,
    telegram_user_id: int,
    checkin_date: date,
) -> Optional[str]:
    stmt = (
        select(DailyCheckin.morning_action_anchor)
        .where(
            DailyCheckin.telegram_user_id == telegram_user_id,
            DailyCheckin.checkin_date == checkin_date,
            DailyCheckin.period.in_([CheckinPeriod.morning, "morning"]),
        )
        .order_by(DailyCheckin.id.desc())
    )
    res = await session.execute(stmt)
    return res.scalars().first()


async def calculate_user_streak(session: AsyncSession, telegram_user_id: int) -> Tuple[int, int]:
    stmt = (
        select(DailyCheckin.checkin_date)
        .where(DailyCheckin.telegram_user_id == telegram_user_id)
        .distinct()
        .order_by(desc(DailyCheckin.checkin_date))
    )
    res = await session.execute(stmt)
    raw_dates = [row[0] for row in res.all()]

    if not raw_dates:
        return 0, 0

    dates = []
    for d in raw_dates:
        if hasattr(d, "date"):
            dates.append(d.date())
        else:
            dates.append(d)

    today = date.today()
    current_streak = 0
    check_day = today

    if dates[0] == today:
        current_streak = 1
        check_day = today - timedelta(days=1)
    elif dates[0] == today - timedelta(days=1):
        current_streak = 1
        check_day = today - timedelta(days=2)
    else:
        current_streak = 0

    if current_streak > 0:
        date_set = set(dates)
        while check_day in date_set:
            current_streak += 1
            check_day -= timedelta(days=1)

    max_streak = 0
    temp_streak = 0
    sorted_unique = sorted(set(dates))
    if sorted_unique:
        temp_streak = 1
        max_streak = 1
        for i in range(1, len(sorted_unique)):
            if sorted_unique[i] - sorted_unique[i - 1] == timedelta(days=1):
                temp_streak += 1
                max_streak = max(max_streak, temp_streak)
            else:
                temp_streak = 1

    return current_streak, max(max_streak, current_streak)


DOMAIN_PRETTY_MAP = {
    "cognitive": "🧠 Робота/Навчання",
    "physical": "🏃 Спорт/Рух",
    "social": "👥 Соціум",
    "screen": "📱 Екрани",
    "rest": "🔋 Відпочинок",
    "routine": "🧹 Побут",
    "stress": "⚡ Стресори",
}


async def get_weekly_stats(
    session: AsyncSession,
    telegram_user_id: int,
    days: int = 7,
) -> Dict[str, Any]:
    start_date = date.today() - timedelta(days=days - 1)

    all_time_stmt = select(func.count(DailyCheckin.id)).where(DailyCheckin.telegram_user_id == telegram_user_id)
    total_all_time = (await session.execute(all_time_stmt)).scalar() or 0

    stmt = (
        select(DailyCheckin)
        .where(
            DailyCheckin.telegram_user_id == telegram_user_id,
            DailyCheckin.checkin_date >= start_date,
        )
        .order_by(DailyCheckin.checkin_date.asc())
    )
    res = await session.execute(stmt)
    records = res.scalars().all()

    morning_by_date = {}
    evening_by_date = {}

    for r in records:
        period_str = r.period.value if hasattr(r.period, "value") else str(r.period)
        if period_str == "morning":
            morning_by_date[r.checkin_date] = r
        elif period_str == "evening":
            evening_by_date[r.checkin_date] = r

    m_count = len(morning_by_date)
    e_count = len(evening_by_date)

    sleep_hours_list = [r.sleep_hours for r in morning_by_date.values() if r.sleep_hours is not None]
    sleep_quality_list = [r.sleep_quality for r in morning_by_date.values() if r.sleep_quality is not None]
    morning_mood_list = [r.morning_mood for r in morning_by_date.values() if r.morning_mood is not None]
    resistance_list = [r.morning_resistance for r in morning_by_date.values() if r.morning_resistance is not None]
    anxiety_list = [r.morning_anxiety for r in morning_by_date.values() if r.morning_anxiety is not None]

    avg_sleep_hours = round(sum(sleep_hours_list) / len(sleep_hours_list), 1) if sleep_hours_list else None
    avg_sleep_quality = round(sum(sleep_quality_list) / len(sleep_quality_list), 1) if sleep_quality_list else None
    avg_morning_mood = round(sum(morning_mood_list) / len(morning_mood_list), 1) if morning_mood_list else None
    avg_resistance = round(sum(resistance_list) / len(resistance_list), 1) if resistance_list else None
    avg_anxiety = round(sum(anxiety_list) / len(anxiety_list), 1) if anxiety_list else None

    evening_mood_list = [r.evening_mood for r in evening_by_date.values() if r.evening_mood is not None]
    avg_evening_mood = round(sum(evening_mood_list) / len(evening_mood_list), 1) if evening_mood_list else None

    mood_deltas = []
    for d, m_rec in morning_by_date.items():
        if d in evening_by_date:
            e_rec = evening_by_date[d]
            if e_rec.evening_mood is not None and m_rec.morning_mood is not None:
                mood_deltas.append(e_rec.evening_mood - m_rec.morning_mood)
    avg_mood_delta = round(sum(mood_deltas) / len(mood_deltas), 2) if mood_deltas else None

    domain_counter = Counter()
    for e_rec in evening_by_date.values():
        if e_rec.activity_domains:
            domain_counter.update(e_rec.activity_domains)
    top_domains = [
        f"{DOMAIN_PRETTY_MAP.get(k, k)} ({cnt})"
        for k, cnt in domain_counter.most_common(3)
    ]

    social_charged = 0
    social_drained = 0
    for e_rec in evening_by_date.values():
        st = (e_rec.social_state or "").lower()
        if any(w in st for w in ["charge", "solitude", "підняло", "відновив"]):
            social_charged += 1
        elif any(w in st for w in ["drain", "alienation", "isolation", "виснажило", "пригнітило", "сам"]):
            social_drained += 1

    emotion_counter = Counter()
    for e_rec in evening_by_date.values():
        emo = e_rec.dominant_emotion
        if emo:
            emotion_counter.update([emo])
    top_emotion = emotion_counter.most_common(1)[0][0] if emotion_counter else None

    current_streak, max_streak = await calculate_user_streak(session, telegram_user_id)

    return {
        "days": days,
        "total_all_time": total_all_time,
        "current_streak": current_streak,
        "max_streak": max_streak,
        "morning_count": m_count,
        "evening_count": e_count,
        "avg_sleep_hours": avg_sleep_hours,
        "avg_sleep_quality": avg_sleep_quality,
        "avg_morning_mood": avg_morning_mood,
        "avg_resistance": avg_resistance,
        "avg_anxiety": avg_anxiety,
        "avg_evening_mood": avg_evening_mood,
        "avg_mood_delta": avg_mood_delta,
        "top_domains": top_domains,
        "social_charged": social_charged,
        "social_drained": social_drained,
        "top_emotion": top_emotion,
    }


async def delete_user_checkins(session: AsyncSession, telegram_user_id: int) -> int:
    stmt = delete(DailyCheckin).where(DailyCheckin.telegram_user_id == telegram_user_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


# ==========================================
# 📊 ЕКСПОРТ В CSV
# ==========================================

async def export_all_checkins_csv(session: AsyncSession) -> str:
    stmt = select(DailyCheckin).order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.period)
    res = await session.execute(stmt)
    checkins = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, dialect="excel")

    headers = [
        "id", "telegram_user_id", "checkin_date", "period", "sleep_hours",
        "sleep_quality", "morning_mood", "morning_resistance", "morning_anxiety",
        "morning_thought", "morning_action_anchor", "evening_mood",
        "activity_domains", "action_result", "social_state", "dominant_emotion",
        "emotion_intensity", "cognitive_closure", "raw_payload", "created_at",
    ]
    writer.writerow(headers)

    for c in checkins:
        writer.writerow([
            c.id,
            c.telegram_user_id,
            c.checkin_date.isoformat() if c.checkin_date else "",
            c.period.value if hasattr(c.period, "value") else str(c.period),
            c.sleep_hours if c.sleep_hours is not None else "",
            c.sleep_quality if c.sleep_quality is not None else "",
            c.morning_mood if c.morning_mood is not None else "",
            c.morning_resistance if c.morning_resistance is not None else "",
            c.morning_anxiety if c.morning_anxiety is not None else "",
            c.morning_thought or "",
            c.morning_action_anchor or "",
            c.evening_mood if c.evening_mood is not None else "",
            ";".join(c.activity_domains) if c.activity_domains else "",
            c.action_result or "",
            c.social_state or "",
            c.dominant_emotion or "",
            c.emotion_intensity if c.emotion_intensity is not None else "",
            c.cognitive_closure or "",
            c.raw_payload if c.raw_payload is not None else "",
            c.created_at.isoformat() if c.created_at else "",
        ])

    return output.getvalue()


async def export_users_csv(session: AsyncSession) -> str:
    stmt = select(User).order_by(User.id)
    res = await session.execute(stmt)
    users = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, dialect="excel")

    headers = [
        "id", "telegram_user_id", "first_name", "username",
        "timezone", "morning_reminder_time", "evening_reminder_time",
        "is_onboarded", "is_active", "created_at",
    ]
    writer.writerow(headers)

    for u in users:
        writer.writerow([
            u.id,
            u.telegram_user_id,
            u.first_name or "",
            u.username or "",
            u.timezone,
            getattr(u, "morning_reminder_time", "08:00"),
            getattr(u, "evening_reminder_time", "22:00"),
            getattr(u, "is_onboarded", True),
            u.is_active,
            u.created_at.isoformat() if u.created_at else "",
        ])

    return output.getvalue()


async def export_user_checkins_csv(session: AsyncSession, telegram_user_id: int) -> str:
    stmt = (
        select(DailyCheckin)
        .where(DailyCheckin.telegram_user_id == telegram_user_id)
        .order_by(DailyCheckin.checkin_date.desc(), DailyCheckin.period)
    )
    res = await session.execute(stmt)
    checkins = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, dialect="excel")

    headers = [
        "checkin_date", "period", "sleep_hours", "sleep_quality",
        "morning_mood", "morning_resistance", "morning_anxiety",
        "morning_thought", "morning_action_anchor", "evening_mood",
        "activity_domains", "action_result", "social_state", "dominant_emotion",
        "emotion_intensity", "cognitive_closure", "raw_payload", "created_at",
    ]
    writer.writerow(headers)

    for c in checkins:
        writer.writerow([
            c.checkin_date.isoformat() if c.checkin_date else "",
            c.period.value if hasattr(c.period, "value") else str(c.period),
            c.sleep_hours if c.sleep_hours is not None else "",
            c.sleep_quality if c.sleep_quality is not None else "",
            c.morning_mood if c.morning_mood is not None else "",
            c.morning_resistance if c.morning_resistance is not None else "",
            c.morning_anxiety if c.morning_anxiety is not None else "",
            c.morning_thought or "",
            c.morning_action_anchor or "",
            c.evening_mood if c.evening_mood is not None else "",
            ";".join(c.activity_domains) if c.activity_domains else "",
            c.action_result or "",
            c.social_state or "",
            c.dominant_emotion or "",
            c.emotion_intensity if c.emotion_intensity is not None else "",
            c.cognitive_closure or "",
            c.raw_payload if c.raw_payload is not None else "",
            c.created_at.isoformat() if c.created_at else "",
        ])

    return output.getvalue()