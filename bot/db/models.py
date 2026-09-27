import enum
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


class CheckinPeriod(str, enum.Enum):
    morning = "morning"
    evening = "evening"


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    checkin_date: Mapped[date] = mapped_column(Date, index=True)
    period: Mapped[CheckinPeriod] = mapped_column(Enum(CheckinPeriod))

    # Ранкові показники
    sleep_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sleep_quality: Mapped[int | None] = mapped_column(Integer, nullable=True)     # шкала 1-5
    resistance_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # шкала 1-5
    anxiety_level: Mapped[int | None] = mapped_column(Integer, nullable=True)     # шкала 1-5

    # Вечірні показники
    day_fact: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)        # шкала 1-5
    social_contact: Mapped[bool | None] = mapped_column(nullable=True)

    # Резервне поле для збереження будь-яких додаткових відповідей у форматі JSON
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())