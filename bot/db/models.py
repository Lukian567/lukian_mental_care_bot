import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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
    
    morning_reminder_time: Mapped[str] = mapped_column(String(5), default="08:00", nullable=False)
    evening_reminder_time: Mapped[str] = mapped_column(String(5), default="22:00", nullable=False)
    is_onboarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class DailyCheckin(Base):
    __tablename__ = "daily_checkins"

    # 🔑 Службові поля (4 поля)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    checkin_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    period: Mapped[CheckinPeriod] = mapped_column(
        Enum(CheckinPeriod, name="checkin_period_enum", create_type=False),
        nullable=False,
    )

    # 🌅 Ранок (7 метрик протоколу)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    sleep_quality: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    morning_mood: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    morning_resistance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    morning_anxiety: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    morning_thought: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    morning_action_anchor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 🌙 Вечір (7 метрик протоколу)
    evening_mood: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    activity_domains: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    action_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    social_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dominant_emotion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotion_intensity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cognitive_closure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 💾 Аудит-лог та системний час
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )