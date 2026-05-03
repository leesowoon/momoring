from dataclasses import dataclass


INVALID_PAYLOAD = "invalid_payload"
SESSION_NOT_FOUND = "session_not_found"
STT_FAILED = "stt_failed"
RESPOND_FAILED = "respond_failed"
TTS_FAILED = "tts_failed"
UNKNOWN_EVENT = "unknown_event"
INTERNAL_ERROR = "internal_error"


_ERROR_MESSAGES = {
    INVALID_PAYLOAD: "Invalid request payload.",
    SESSION_NOT_FOUND: "Session not found.",
    STT_FAILED: "Speech transcription failed.",
    RESPOND_FAILED: "Response generation failed.",
    TTS_FAILED: "Speech synthesis failed.",
    UNKNOWN_EVENT: "Unknown websocket event.",
    INTERNAL_ERROR: "Internal server error.",
}


@dataclass(frozen=True)
class ErrorDetail:
    code: str
    message: str
    trace_id: str


def message_for(code: str) -> str:
    return _ERROR_MESSAGES.get(code, "Unhandled error.")


def make_error_payload(code: str, trace_id: str, message: str | None = None) -> dict[str, dict[str, str]]:
    return {
        "error": {
            "code": code,
            "message": message or message_for(code),
            "trace_id": trace_id,
        }
    }


def make_ws_error_payload(code: str, trace_id: str, message: str | None = None) -> dict[str, object]:
    return {
        "type": "error",
        "error": {
            "code": code,
            "message": message or message_for(code),
            "trace_id": trace_id,
        },
    }
