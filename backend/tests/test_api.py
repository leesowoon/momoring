from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_start_session() -> None:
    res = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    assert res.status_code == 200
    body = res.json()
    assert "session_id" in body
    assert "ws_url" in body


def test_safety_block() -> None:
    res = client.post("/v1/safety/check", json={"text": "자해 하고 싶어"})
    assert res.status_code == 200
    assert res.json()["safe"] is False
