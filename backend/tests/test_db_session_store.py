import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from app.db.session_store import DBSessionStore


@pytest.fixture
def store() -> DBSessionStore:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    return DBSessionStore(factory)


def test_create_then_get_returns_session(store: DBSessionStore) -> None:
    store.create("s1", "10-12")
    view = store.get("s1")
    assert view is not None
    assert view.session_id == "s1"
    assert view.age_group == "10-12"
    assert view.turns == []


def test_get_unknown_session_returns_none(store: DBSessionStore) -> None:
    assert store.get("nope") is None


def test_append_turn_persists_in_order(store: DBSessionStore) -> None:
    store.create("s1", "10-12")
    store.append_turn("s1", "Q1", "A1", False)
    store.append_turn("s1", "Q2", "A2", True)

    view = store.get("s1")
    assert view is not None
    assert [(t.user_text, t.bot_text, t.blocked) for t in view.turns] == [
        ("Q1", "A1", False),
        ("Q2", "A2", True),
    ]


def test_append_turn_to_unknown_session_is_silent_noop(store: DBSessionStore) -> None:
    store.append_turn("missing", "u", "b", False)
    assert store.get("missing") is None


def test_append_feedback_persists(store: DBSessionStore) -> None:
    store.create("s1", "10-12")
    store.append_feedback("s1", "turn-1", "up", "도움됨")

    view = store.get("s1")
    assert view is not None
    assert len(view.feedbacks) == 1
    assert view.feedbacks[0].turn_id == "turn-1"
    assert view.feedbacks[0].rating == "up"
    assert view.feedbacks[0].reason == "도움됨"


def test_as_dict_matches_json_store_shape(store: DBSessionStore) -> None:
    store.create("s1", "13-15")
    store.append_turn("s1", "Q", "A", False)
    store.append_feedback("s1", "turn-0", "down", None)

    body = store.as_dict("s1")
    assert body is not None
    assert body["session_id"] == "s1"
    assert body["age_group"] == "13-15"
    assert body["turn_count"] == 1
    assert body["feedback_count"] == 1
    assert body["turns"][0]["user_text"] == "Q"
    assert body["feedbacks"][0]["rating"] == "down"


def test_as_dict_unknown_session_returns_none(store: DBSessionStore) -> None:
    assert store.as_dict("nope") is None
