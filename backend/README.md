# Momoring MVP Backend (FastAPI)

## 1) Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
```

For local development including lint/typecheck/pre-commit:
```bash
pip install -r requirements-dev.txt
pre-commit install   # run from repo root
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

## 3a) Lint / Typecheck
```bash
cd backend
ruff check .
ruff format --check .
mypy
```
Pre-commit runs ruff + mypy automatically on staged files; CI runs all three.

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

## WebSocket Event Contract
Client:
- `audio_chunk` (`session_id`, `audio_base64`)
- `end_of_utterance` (`session_id`, `text` optional)

Server order (normal flow):
1. `partial_transcript`
2. `final_transcript`
3. `bot_text`
4. `tts_ready`

Server error handling:
- missing `session_id` -> `{"type":"error","message":"missing session_id"}`
- unknown event -> `{"type":"error","message":"unknown event"}`
- malformed payload -> `{"type":"error","message":"malformed payload"}`
- provider failures -> `stt_failed` / `respond_failed` / `tts_failed`

## Provider Modes

### LLM (existing)
- Default: mock GPT + mock Claude fallback
- Real mode: `USE_REAL_PROVIDERS=true` with API keys

### STT (P1)
- Default: `MockSTTProvider`
- Real mode: `USE_REAL_STT=true` + `OPENAI_API_KEY`
- Model env: `OPENAI_STT_MODEL` (default `whisper-1`)

### TTS (P2)
- Default: `MockTTSProvider` (stable `/audio/...` URL)
- Real mode: `USE_REAL_TTS=true` + `OPENAI_API_KEY`
- Model/voice env: `OPENAI_TTS_MODEL`, `OPENAI_TTS_VOICE`
- Output dir env: `AUDIO_OUTPUT_DIR` (default `.data/audio`)

Generated audio is served at `/audio/<filename>.mp3`.

## Notes
- Keep `.env` and `.data/` out of git.
- Mock mode is the default and works offline-friendly.
