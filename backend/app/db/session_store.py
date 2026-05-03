"""DB-backed counterpart of the JSON SessionStore.

Mirrors the public surface of `app.services.session_store.SessionStore`
(`create`, `get`, `append_turn`, `append_feedback`, `as_dict`) so it can
become a drop-in replacement once we switch the FastAPI wiring.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from .models import FeedbackRow, SessionRow, TurnRow


@dataclass
class TurnView:
    user_text: str
    bot_text: str
    blocked: bool
    created_at: str


@dataclass
class FeedbackView:
    turn_id: str
    rating: str
    reason: str | None
    created_at: str


@dataclass
class SessionView:
    session_id: str
    age_group: str
    started_at: str
    turns: list[TurnView]
    feedbacks: list[FeedbackView]


class DBSessionStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, session_id: str, age_group: str) -> SessionView:
        with self._session_factory() as db:
            row = SessionRow(id=session_id, age_group=age_group)
            db.add(row)
            db.commit()
            db.refresh(row)
            return _to_view(row)

    def get(self, session_id: str) -> SessionView | None:
        with self._session_factory() as db:
            row = db.get(SessionRow, session_id)
            if row is None:
                return None
            return _to_view(row)

    def append_turn(
        self, session_id: str, user_text: str, bot_text: str, blocked: bool
    ) -> None:
        with self._session_factory() as db:
            session = db.get(SessionRow, session_id)
            if session is None:
                return
            db.add(
                TurnRow(
                    session_id=session_id,
                    user_text=user_text,
                    bot_text=bot_text,
                    blocked=blocked,
                )
            )
            db.commit()

    def append_feedback(
        self, session_id: str, turn_id: str, rating: str, reason: str | None
    ) -> None:
        with self._session_factory() as db:
            session = db.get(SessionRow, session_id)
            if session is None:
                return
            db.add(
                FeedbackRow(
                    session_id=session_id,
                    turn_id=turn_id,
                    rating=rating,
                    reason=reason,
                )
            )
            db.commit()

    def as_dict(self, session_id: str) -> dict[str, Any] | None:
        with self._session_factory() as db:
            row = db.execute(
                select(SessionRow).where(SessionRow.id == session_id)
            ).scalar_one_or_none()
            if row is None:
                return None
            view = _to_view(row)
            return {
                "session_id": view.session_id,
                "age_group": view.age_group,
                "started_at": view.started_at,
                "turn_count": len(view.turns),
                "feedback_count": len(view.feedbacks),
                "turns": [
                    {
                        "user_text": t.user_text,
                        "bot_text": t.bot_text,
                        "blocked": t.blocked,
                        "created_at": t.created_at,
                    }
                    for t in view.turns
                ],
                "feedbacks": [
                    {
                        "turn_id": f.turn_id,
                        "rating": f.rating,
                        "reason": f.reason,
                        "created_at": f.created_at,
                    }
                    for f in view.feedbacks
                ],
            }


def _to_view(row: SessionRow) -> SessionView:
    return SessionView(
        session_id=row.id,
        age_group=row.age_group,
        started_at=row.started_at.isoformat(),
        turns=[
            TurnView(
                user_text=t.user_text,
                bot_text=t.bot_text,
                blocked=t.blocked,
                created_at=t.created_at.isoformat(),
            )
            for t in row.turns
        ],
        feedbacks=[
            FeedbackView(
                turn_id=f.turn_id,
                rating=f.rating,
                reason=f.reason,
                created_at=f.created_at.isoformat(),
            )
            for f in row.feedbacks
        ],
    )
