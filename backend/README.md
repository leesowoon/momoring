# Momoring MVP Backend (FastAPI)

## 1) Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
```

## 2) Run
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## 3) Test
```bash
cd backend
pytest -q
```

## 4) Local Demo
1. Start backend (`uvicorn app.main:app --reload --port 8000`)
2. Open `http://localhost:8000/static/demo.html`
3. Click **Start Session**
4. Click **Connect WebSocket**
5. Enter text and send with WS or HTTP fallback button
6. Confirm transcript, bot response, and TTS playback

## Implemented Endpoints
- `GET /health`
- `GET /v1/meta/provider`
- `POST /v1/sts/session/start`
- `GET /v1/sts/session/{session_id}`
- `POST /v1/sts/respond`
- `POST /v1/tts/speak`
- `POST /v1/safety/check`
- `POST /v1/feedback`
- `WS /v1/sts/stream`

## REST Error Contract
Handled REST errors use a shared envelope and include the same trace id as the `X-Trace-Id` response header:

```json
{
  "error": {
    "code": "session_not_found",
    "message": "Session not found.",
    "trace_id": "..."
  }
}
```

Validation failures use `code: "invalid_payload"` with HTTP 422.

## WebSocket Event Contract
Client:
- `audio_chunk` (`session_id`, `audio_base64`)
- `end_of_utterance` (`session_id`, `text` optional)

Server order (normal flow):
1. `partial_transcript`
2. `final_transcript`
3. `bot_text`
4. `tts_ready`

Server error handling uses a shared error envelope:

```json
{
  "type": "error",
  "error": {
    "code": "unknown_event",
    "message": "Unknown websocket event.",
    "trace_id": "..."
  }
}
```

Common error codes:
- `invalid_payload` — missing `session_id` or malformed payload
- `session_not_found` — unknown session id
- `unknown_event` — unsupported WebSocket event type
- `stt_failed` — speech transcription failed
- `respond_failed` — response generation failed
- `tts_failed` — speech synthesis failed
- `internal_error` — unexpected server error

## Provider Modes

### LLM (existing)
- Default: mock GPT + mock Claude fallback
- Real mode: `USE_REAL_PROVIDERS=true` with API keys

### STT (P1)
- Default: `MockSTTProvider`
- Real mode: `USE_REAL_STT=true` + `OPENAI_API_KEY`
- Model env: `OPENAI_STT_MODEL` (default `whisper-1`)

### TTS (P2)
- Default: `MockTTSProvider` returns a stable placeholder `/audio/...` URL. It is useful for API contract tests, but it does not create a playable audio file.
- Real mode: `USE_REAL_TTS=true` + `OPENAI_API_KEY`
- Model/voice env: `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`
- Output dir env: `AUDIO_OUTPUT_DIR` (default `.data/audio`)

Generated real-provider audio is served at `/audio/<filename>.mp3`.

## Notes
- Keep `.env` and `.data/` out of git.
- Mock mode is the default and works offline-friendly.
- Use real TTS mode for browser audio playback verification.
