from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_ws_audio_chunk_and_end_of_utterance_flow() -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    session_id = start.json()["session_id"]

    with client.websocket_connect("/v1/sts/stream") as ws:
        ws.send_json({"type": "audio_chunk", "session_id": session_id, "audio_base64": "abc"})
        partial = ws.receive_json()
        assert partial["type"] == "partial_transcript"

        ws.send_json({"type": "end_of_utterance", "session_id": session_id, "text": "안녕"})
        final_msg = ws.receive_json()
        bot_msg = ws.receive_json()
        tts_msg = ws.receive_json()

        assert final_msg["type"] == "final_transcript"
        assert bot_msg["type"] == "bot_text"
        assert tts_msg["type"] == "tts_ready"


def test_ws_missing_session_id_returns_standard_error() -> None:
    with client.websocket_connect("/v1/sts/stream") as ws:
        ws.send_json({"type": "audio_chunk", "audio_base64": "abc"})
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["error"]["code"] == "invalid_payload"
        assert msg["error"]["trace_id"]


def test_ws_unknown_event_returns_standard_error() -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    session_id = start.json()["session_id"]

    with client.websocket_connect("/v1/sts/stream") as ws:
        ws.send_json({"type": "unknown", "session_id": session_id})
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["error"]["code"] == "unknown_event"
        assert msg["error"]["trace_id"]


def test_ws_malformed_payload_returns_standard_error() -> None:
    with client.websocket_connect("/v1/sts/stream") as ws:
        ws.send_text("not-json")
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["error"]["code"] == "invalid_payload"


def test_ws_stt_error_does_not_crash_flow(monkeypatch) -> None:
    start = client.post("/v1/sts/session/start", json={"age_group": "10-12"})
    session_id = start.json()["session_id"]

    async def failing_transcribe(_: str) -> str:
        raise RuntimeError("boom")

    from app import main

    monkeypatch.setattr(main.stt_provider, "transcribe_chunk", failing_transcribe)

    with client.websocket_connect("/v1/sts/stream") as ws:
        ws.send_json({"type": "audio_chunk", "session_id": session_id, "audio_base64": "abc"})
        err = ws.receive_json()
        assert err["type"] == "error"
        assert err["error"]["code"] == "stt_failed"
        assert err["error"]["trace_id"]

        ws.send_json({"type": "end_of_utterance", "session_id": session_id, "text": "계속"})
        assert ws.receive_json()["type"] == "final_transcript"
        assert ws.receive_json()["type"] == "bot_text"
        assert ws.receive_json()["type"] == "tts_ready"
