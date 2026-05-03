import json
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


def test_missing_file_loads_empty_store(tmp_path: Path) -> None:
    db_file = tmp_path / "missing.json"
    store = SessionStore(str(db_file))
    assert store.as_dict("any") is None


def test_corrupt_json_is_backed_up_and_store_starts_empty(tmp_path: Path) -> None:
    db_file = tmp_path / "sessions.json"
    db_file.write_text("{broken-json", encoding="utf-8")

    store = SessionStore(str(db_file))
    assert store.as_dict("any") is None

    backups = list(tmp_path.glob("sessions.json.corrupt.*"))
    assert backups, "expected corrupt backup file"


def test_invalid_root_structure_is_backed_up(tmp_path: Path) -> None:
    db_file = tmp_path / "sessions.json"
    db_file.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

    store = SessionStore(str(db_file))
    assert store.as_dict("any") is None
    backups = list(tmp_path.glob("sessions.json.corrupt.*"))
    assert backups


def test_persist_write_is_readable_json(tmp_path: Path) -> None:
    db_file = tmp_path / "sessions.json"

    store = SessionStore(str(db_file))
    store.create("s3", "10-12")
    store.append_turn("s3", "질문", "답", False)

    raw = json.loads(db_file.read_text(encoding="utf-8"))
    assert "s3" in raw
    assert raw["s3"]["session_id"] == "s3"
