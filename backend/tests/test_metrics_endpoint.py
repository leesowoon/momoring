from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_metrics_endpoint_returns_prometheus_text() -> None:
    res = client.get("/metrics")
    assert res.status_code == 200

    body = res.text
    assert "# TYPE momoring_sessions_started_total counter" in body
    assert "# TYPE momoring_sts_latency_ms histogram" in body
    assert "# TYPE momoring_active_sessions gauge" in body


def test_session_start_increments_counter() -> None:
    before = client.get("/metrics").text
    client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    after = client.get("/metrics").text

    def _value_of(text: str, metric: str) -> float:
        for line in text.splitlines():
            if line.startswith(f"{metric} "):
                return float(line.split()[-1])
        return 0.0

    assert _value_of(after, "momoring_sessions_started_total") > _value_of(
        before, "momoring_sessions_started_total"
    )


def test_blocked_respond_increments_safety_counter() -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    session_id = start.json()["session_id"]

    client.post("/v1/sts/respond", json={"session_id": session_id, "text": "자해 하고 싶어"})
    body = client.get("/metrics").text

    assert "momoring_safety_block_total" in body
    assert 'category="self_harm"' in body
    assert 'source="input"' in body
