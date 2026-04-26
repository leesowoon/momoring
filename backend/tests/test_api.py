from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.headers.get("X-Trace-Id")


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


def test_tts_speak_returns_audio_url() -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    session_id = start.json()["session_id"]

    res = client.post("/v1/tts/speak", json={"session_id": session_id, "text": "안녕"})
    assert res.status_code == 200
    assert res.json()["audio_url"].startswith("/audio/")


def test_rest_session_not_found_error_shape() -> None:
    res = client.get("/v1/sts/session/does-not-exist")
    assert res.status_code == 404
    body = res.json()
    assert body["error"]["code"] == "session_not_found"
    assert body["error"]["message"]
    assert body["error"]["trace_id"]
    assert res.headers.get("X-Trace-Id") == body["error"]["trace_id"]


def test_rest_validation_error_shape() -> None:
    res = client.post("/v1/sts/session/start", json={"age_group": "invalid"})
    assert res.status_code == 422
    body = res.json()
    assert body["error"]["code"] == "invalid_payload"
    assert body["error"]["message"]
    assert body["error"]["trace_id"]
    assert res.headers.get("X-Trace-Id") == body["error"]["trace_id"]
