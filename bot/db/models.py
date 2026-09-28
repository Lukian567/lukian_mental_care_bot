import enum
from datetime import date, datetime
from typing import Optional, Any
from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Integer,
    String,
    Boolean,
    Enum,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from bot.db.base import Base


class CheckinPeriod(str, enum.Enum):
    morning = "morning"
    evening = "evening"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Europe/Warsaw", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    checkin_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    period: Mapped[CheckinPeriod] = mapped_column(
        Enum(CheckinPeriod, name="checkin_period_enum", create_type=False),
        nullable=False,
    )

    # 🌅 РАНОК
    sleep_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sleep_quality: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    morning_mood: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resistance_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    anxiety_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    morning_thought: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    micro_action: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # 🌙 ВЕЧІР
    day_fact: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mood_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    action_done: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_quality: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emotion: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emotion_intensity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    compassion: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Додатковий контекст
    raw_payload: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )