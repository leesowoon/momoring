"""SQLAlchemy 2.0 models for sessions / turns / safety events / feedback.

Tables match mvp_technical_design.md sec 6. Class names carry a `Row`
suffix so they don't collide with `sqlalchemy.orm.Session`.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    age_group: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    status: Mapped[str] = mapped_column(String(16), default="active")

    turns: Mapped[list["TurnRow"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TurnRow.created_at",
    )
    feedbacks: Mapped[list["FeedbackRow"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="FeedbackRow.created_at",
    )
    safety_events: Mapped[list["SafetyEventRow"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="SafetyEventRow.created_at",
    )


class TurnRow(Base):
    __tablename__ = "turns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    user_text: Mapped[str] = mapped_column(Text)
    bot_text: Mapped[str] = mapped_column(Text)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped[SessionRow] = relationship(back_populates="turns")


class FeedbackRow(Base):
    __tablename__ = "feedbacks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    turn_id: Mapped[str] = mapped_column(String(64))
    rating: Mapped[str] = mapped_column(String(8))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped[SessionRow] = relationship(back_populates="feedbacks")


class SafetyEventRow(Base):
    __tablename__ = "safety_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("sessions.id", ondelete="CASCADE"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    session: Mapped[SessionRow] = relationship(back_populates="safety_events")
