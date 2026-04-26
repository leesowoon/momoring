from pathlib import Path
from app.services.session_store import SessionStore


def test_create_and_append_turn() -> None:
    store = SessionStore()
    store.create("s1", "10-12")
    store.append_turn("s1", "안녕", "모모링: 안녕!", False)
    store.append_feedback("s1", "t1", "up", "좋아요")

    row = store.as_dict("s1")
    assert row is not None
    assert row["turn_count"] == 1
    assert row["feedback_count"] == 1
    assert row["turns"][0]["user_text"] == "안녕"


def test_persist_and_reload(tmp_path: Path) -> None:
    db_file = tmp_path / "sessions.json"

    store = SessionStore(str(db_file))
    store.create("s2", "7-9")
    store.append_turn("s2", "질문", "답변", False)
    store.append_feedback("s2", "turn-1", "down", "아쉬움")

    reloaded = SessionStore(str(db_file))
    row = reloaded.as_dict("s2")
    assert row is not None
    assert row["turn_count"] == 1
    assert row["feedback_count"] == 1
    assert row["age_group"] == "7-9"
