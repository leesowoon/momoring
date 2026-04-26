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


def test_ws_unknown_event_returns_error() -> None:
    with client.websocket_connect("/v1/sts/stream") as ws:
        ws.send_json({"type": "unknown"})
        msg = ws.receive_json()
        assert msg["type"] == "error"
