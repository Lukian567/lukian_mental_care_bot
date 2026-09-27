from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import DailyCheckin, CheckinPeriod


async def save_checkin(
    session: AsyncSession,
    user_id: int,
    checkin_date: date,
    period: str,
    data: dict,
) -> DailyCheckin:
    """Зберігає сесію чекіну з FSM у таблицю daily_checkins."""
    
    # Використовуємо значення enum у нижньому регістрі або створюємо напряму через конструктор
    try:
        period_enum = CheckinPeriod(period)
    except (ValueError, TypeError):
        # Якщо в моделі назви атрибутів у нижньому регістрі (наприклад, CheckinPeriod.morning)
        period_enum = getattr(CheckinPeriod, period, period)

    checkin = DailyCheckin(
        telegram_user_id=user_id,
        checkin_date=checkin_date,
        period=period_enum,
        sleep_duration_minutes=data.get("sleep_duration_minutes"),
        sleep_quality=data.get("sleep_quality"),
        resistance_level=data.get("resistance_level"),
        anxiety_level=data.get("anxiety_level"),
        day_fact=str(data.get("day_fact", ""))[:500] if data.get("day_fact") else None,
        mood_score=data.get("mood_score"),
        raw_payload=data,
    )

    session.add(checkin)
    await session.commit()
    await session.refresh(checkin)
    return checkin