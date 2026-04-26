from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from threading import Lock
from typing import Any
import json


@dataclass
class Turn:
    user_text: str
    bot_text: str
    blocked: bool
    created_at: str


@dataclass
class Feedback:
    turn_id: str
    rating: str
    reason: str | None
    created_at: str


@dataclass
class SessionRecord:
    session_id: str
    age_group: str
    started_at: str
    turns: list[Turn] = field(default_factory=list)
    feedbacks: list[Feedback] = field(default_factory=list)


class SessionStore:
    def __init__(self, persist_path: str | None = None) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._lock = Lock()
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            self._load()

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return

        raw = json.loads(self._persist_path.read_text(encoding="utf-8"))
        sessions: dict[str, SessionRecord] = {}
        for session_id, row in raw.items():
            turns = [Turn(**t) for t in row.get("turns", [])]
            feedbacks = [Feedback(**f) for f in row.get("feedbacks", [])]
            sessions[session_id] = SessionRecord(
                session_id=row["session_id"],
                age_group=row["age_group"],
                started_at=row["started_at"],
                turns=turns,
                feedbacks=feedbacks,
            )
        self._sessions = sessions

    def _persist(self) -> None:
        if not self._persist_path:
            return

        serializable = {
            sid: {
                "session_id": row.session_id,
                "age_group": row.age_group,
                "started_at": row.started_at,
                "turns": [asdict(t) for t in row.turns],
                "feedbacks": [asdict(f) for f in row.feedbacks],
            }
            for sid, row in self._sessions.items()
        }
        self._persist_path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create(self, session_id: str, age_group: str) -> SessionRecord:
        record = SessionRecord(
            session_id=session_id,
            age_group=age_group,
            started_at=datetime.now(UTC).isoformat(),
        )
        with self._lock:
            self._sessions[session_id] = record
            self._persist()
        return record

    def get(self, session_id: str) -> SessionRecord | None:
        with self._lock:
            return self._sessions.get(session_id)

    def append_turn(self, session_id: str, user_text: str, bot_text: str, blocked: bool) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if not record:
                return
            record.turns.append(
                Turn(
                    user_text=user_text,
                    bot_text=bot_text,
                    blocked=blocked,
                    created_at=datetime.now(UTC).isoformat(),
                )
            )
            self._persist()

    def append_feedback(self, session_id: str, turn_id: str, rating: str, reason: str | None) -> None:
        with self._lock:
            record = self._sessions.get(session_id)
            if not record:
                return
            record.feedbacks.append(
                Feedback(
                    turn_id=turn_id,
                    rating=rating,
                    reason=reason,
                    created_at=datetime.now(UTC).isoformat(),
                )
            )
            self._persist()

    def as_dict(self, session_id: str) -> dict[str, Any] | None:
        record = self.get(session_id)
        if not record:
            return None
        return {
            "session_id": record.session_id,
            "age_group": record.age_group,
            "started_at": record.started_at,
            "turn_count": len(record.turns),
            "feedback_count": len(record.feedbacks),
            "turns": [
                {
                    "user_text": t.user_text,
                    "bot_text": t.bot_text,
                    "blocked": t.blocked,
                    "created_at": t.created_at,
                }
                for t in record.turns
            ],
            "feedbacks": [
                {
                    "turn_id": f.turn_id,
                    "rating": f.rating,
                    "reason": f.reason,
                    "created_at": f.created_at,
                }
                for f in record.feedbacks
            ],
        }
