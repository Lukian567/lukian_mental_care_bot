import csv
import io
from datetime import date, timedelta
from typing import List, Optional

from sqlalchemy import select, func, desc, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import DailyCheckin, CheckinPeriod, User


async def save_checkin(
    session: AsyncSession,
    user_id: int,
    checkin_date: date,
    period: str,
    data: dict,
) -> DailyCheckin:
    """Зберігає сесію чекіну з FSM у таблицю daily_checkins."""
    try:
        period_enum = CheckinPeriod(period)
    except (ValueError, TypeError):
        period_enum = getattr(CheckinPeriod, period, period)

    checkin = DailyCheckin(
        telegram_user_id=user_id,
        checkin_date=checkin_date,
        period=period_enum,
        # 🌅 РАНОК
        sleep_duration_minutes=data.get("sleep_duration_minutes"),
        sleep_quality=data.get("sleep_quality"),
        morning_mood=data.get("morning_mood"),
        resistance_level=data.get("resistance_level"),
        anxiety_level=data.get("anxiety_level"),
        morning_thought=str(data.get("morning_thought", ""))[:500] if data.get("morning_thought") else None,
        micro_action=str(data.get("micro_action", ""))[:500] if data.get("micro_action") else None,
        # 🌙 ВЕЧІР
        day_fact=str(data.get("day_fact", ""))[:500] if data.get("day_fact") else None,
        mood_score=data.get("mood_score"),
        action_done=str(data.get("action_done", ""))[:200] if data.get("action_done") else None,
        contact_quality=str(data.get("contact_quality", ""))[:200] if data.get("contact_quality") else None,
        emotion=str(data.get("emotion", ""))[:100] if data.get("emotion") else None,
        emotion_intensity=data.get("emotion_intensity"),
        compassion=str(data.get("compassion", ""))[:500] if data.get("compassion") else None,
        # Повний JSON контекст
        raw_payload=data,
    )

    session.add(checkin)
    await session.commit()
    await session.refresh(checkin)
    return checkin


async def register_or_update_user(
    session: AsyncSession,
    telegram_user_id: int,
    first_name: Optional[str],
    username: Optional[str],
    timezone: str = "Europe/Warsaw",
) -> User:
    """Реєструє або оновлює користувача."""
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            telegram_user_id=telegram_user_id,
            first_name=first_name,
            username=username,
            timezone=timezone,
            is_active=True,
        )
        session.add(user)
    else:
        user.first_name = first_name
        user.username = username
        user.is_active = True

    await session.commit()
    await session.refresh(user)
    return user


async def update_user_timezone(
    session: AsyncSession,
    telegram_user_id: int,
    timezone: str,
) -> bool:
    """Змінює часовий пояс користувача (Europe/Warsaw або Europe/Kyiv)."""
    stmt = select(User).where(User.telegram_user_id == telegram_user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.timezone = timezone
        await session.commit()
        return True
    return False


async def get_user_timezone(
    session: AsyncSession,
    telegram_user_id: int,
) -> str:
    """Повертає таймзону користувача або Europe/Warsaw за замовчуванням."""
    stmt = select(User.timezone).where(User.telegram_user_id == telegram_user_id)
    result = await session.execute(stmt)
    tz = result.scalar_one_or_none()
    return tz or "Europe/Warsaw"


async def get_active_users_by_timezone(
    session: AsyncSession,
    timezone: str,
) -> List[User]:
    """Повертає список активних користувачів конкретного часового поясу."""
    stmt = select(User).where(User.is_active == True, User.timezone == timezone)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_user_streak(
    session: AsyncSession,
    user_id: int,
    today: date,
) -> tuple[int, int]:
    """Рахує поточний та максимальний стрік чекінів."""
    stmt = (
        select(DailyCheckin.checkin_date)
        .where(DailyCheckin.telegram_user_id == user_id)
        .distinct()
        .order_by(DailyCheckin.checkin_date.desc())
    )
    result = await session.execute(stmt)
    dates = [row[0] for row in result.all()]

    if not dates:
        return 0, 0

    unique_dates = sorted(set(dates), reverse=True)
    yesterday = today - timedelta(days=1)

    # 1. Поточний стрік
    current_streak = 0
    if unique_dates[0] == today:
        expected = today
    elif unique_dates[0] == yesterday:
        expected = yesterday
    else:
        expected = None

    if expected is not None:
        for d in unique_dates:
            if d == expected:
                current_streak += 1
                expected -= timedelta(days=1)
            elif d < expected:
                break

    # 2. Рекордний стрік
    max_streak = 0
    temp_streak = 1
    for i in range(len(unique_dates) - 1):
        if (unique_dates[i] - unique_dates[i + 1]).days == 1:
            temp_streak += 1
        else:
            if temp_streak > max_streak:
                max_streak = temp_streak
            temp_streak = 1
    if temp_streak > max_streak:
        max_streak = temp_streak

    max_streak = max(max_streak, current_streak)
    return current_streak, max_streak


async def get_weekly_stats(
    session: AsyncSession,
    user_id: int,
    days: int = 7,
    today: Optional[date] = None,
) -> dict:
    """Збирає статистику та стріки."""
    if today is None:
        today = date.today()

    start_date = today - timedelta(days=days - 1)

    stmt = (
        select(DailyCheckin)
        .where(
            DailyCheckin.telegram_user_id == user_id,
            DailyCheckin.checkin_date >= start_date,
            DailyCheckin.checkin_date <= today,
        )
        .order_by(DailyCheckin.checkin_date.asc())
    )
    result = await session.execute(stmt)
    records = result.scalars().all()

    morning_records = [r for r in records if r.period == CheckinPeriod.morning]
    evening_records = [r for r in records if r.period == CheckinPeriod.evening]

    sleep_minutes = [
        r.sleep_duration_minutes
        for r in morning_records
        if r.sleep_duration_minutes is not None
    ]
    avg_sleep_hours = (
        round(sum(sleep_minutes) / len(sleep_minutes) / 60, 1)
        if sleep_minutes
        else None
    )

    sleep_q = [r.sleep_quality for r in morning_records if r.sleep_quality is not None]
    avg_sleep_quality = round(sum(sleep_q) / len(sleep_q), 1) if sleep_q else None

    resist = [
        r.resistance_level for r in morning_records if r.resistance_level is not None
    ]
    avg_resistance = round(sum(resist) / len(resist), 1) if resist else None

    anx = [r.anxiety_level for r in morning_records if r.anxiety_level is not None]
    avg_anxiety = round(sum(anx) / len(anx), 1) if anx else None

    m_moods = [
        r.morning_mood
        for r in morning_records
        if r.morning_mood is not None
    ]
    avg_morning_mood = round(sum(m_moods) / len(m_moods), 1) if m_moods else None

    e_moods = [r.mood_score for r in evening_records if r.mood_score is not None]
    avg_evening_mood = round(sum(e_moods) / len(e_moods), 1) if e_moods else None

    emotions = [
        r.emotion
        for r in evening_records
        if r.emotion and r.emotion != "Пропущено"
    ]
    top_emotion = max(set(emotions), key=emotions.count) if emotions else None

    current_streak, max_streak = await get_user_streak(session, user_id, today)

    return {
        "days": days,
        "morning_count": len(morning_records),
        "evening_count": len(evening_records),
        "avg_sleep_hours": avg_sleep_hours,
        "avg_sleep_quality": avg_sleep_quality,
        "avg_morning_mood": avg_morning_mood,
        "avg_resistance": avg_resistance,
        "avg_anxiety": avg_anxiety,
        "avg_evening_mood": avg_evening_mood,
        "top_emotion": top_emotion,
        "current_streak": current_streak,
        "max_streak": max_streak,
    }


async def delete_user_checkins(session: AsyncSession, user_id: int) -> int:
    """Видаляє всі чекіни користувача з бази даних."""
    stmt = delete(DailyCheckin).where(DailyCheckin.telegram_user_id == user_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount


async def export_all_checkins_csv(session: AsyncSession) -> str:
    """Генерує повний CSV-звіт з усіма записами чекінів."""
    stmt = select(DailyCheckin).order_by(DailyCheckin.id.asc())
    result = await session.execute(stmt)
    records = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    headers = [
        "id",
        "telegram_user_id",
        "checkin_date",
        "period",
        "sleep_duration_minutes",
        "sleep_quality",
        "morning_mood",
        "resistance_level",
        "anxiety_level",
        "morning_thought",
        "micro_action",
        "day_fact",
        "mood_score",
        "action_done",
        "contact_quality",
        "emotion",
        "emotion_intensity",
        "compassion",
        "created_at",
    ]
    writer.writerow(headers)

    for r in records:
        writer.writerow([
            r.id,
            r.telegram_user_id,
            r.checkin_date.isoformat() if r.checkin_date else None,
            r.period.value if hasattr(r.period, "value") else str(r.period),
            r.sleep_duration_minutes,
            r.sleep_quality,
            r.morning_mood,
            r.resistance_level,
            r.anxiety_level,
            r.morning_thought,
            r.micro_action,
            r.day_fact,
            r.mood_score,
            r.action_done,
            r.contact_quality,
            r.emotion,
            r.emotion_intensity,
            r.compassion,
            r.created_at.isoformat() if getattr(r, "created_at", None) else None,
        ])

    return output.getvalue()


async def export_users_csv(session: AsyncSession) -> str:
    """Генерує CSV-звіт з усіма зареєстрованими користувачами."""
    stmt = select(User).order_by(User.id.asc())
    result = await session.execute(stmt)
    records = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    headers = ["id", "telegram_user_id", "first_name", "username", "timezone", "is_active", "created_at"]
    writer.writerow(headers)

    for u in records:
        writer.writerow([
            u.id,
            u.telegram_user_id,
            u.first_name,
            u.username,
            u.timezone,
            u.is_active,
            u.created_at.isoformat() if getattr(u, "created_at", None) else None,
        ])

    return output.getvalue()