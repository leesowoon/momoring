from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_e2e_start_respond_session_detail() -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    respond = client.post("/v1/sts/respond", json={"session_id": session_id, "text": "공룡이 뭐야?"})
    assert respond.status_code == 200
    assert respond.json()["blocked"] is False

    detail = client.get(f"/v1/sts/session/{session_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["turn_count"] >= 1
    assert body["turns"][0]["user_text"] == "공룡이 뭐야?"


def test_e2e_safety_blocked_flow() -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "13-15"})
    session_id = start.json()["session_id"]

    respond = client.post("/v1/sts/respond", json={"session_id": session_id, "text": "자해 하고 싶어"})
    assert respond.status_code == 200
    body = respond.json()
    assert body["blocked"] is True
    assert "안전" in body["text"]


def test_provider_meta_exposes_mode() -> None:
    meta = client.get("/v1/meta/provider")
    assert meta.status_code == 200
    body = meta.json()
    assert "llm_primary" in body
    assert "llm_fallback" in body
    assert "use_real_providers" in body


def test_feedback_saved_in_session_detail() -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    session_id = start.json()["session_id"]

    res = client.post(
        "/v1/feedback",
        json={
            "session_id": session_id,
            "turn_id": "turn-1",
            "rating": "up",
            "reason": "도움됨",
        },
    )
    assert res.status_code == 200

    detail = client.get(f"/v1/sts/session/{session_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["feedback_count"] >= 1
    assert body["feedbacks"][0]["turn_id"] == "turn-1"
