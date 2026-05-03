# Codex Execution Plan — Momoring MVP Next Steps

## Context

Momoring currently has a merged FastAPI MVP backend that includes:

- REST endpoints for health, provider metadata, session start/detail, STS respond, TTS speak, safety check, and feedback
- WebSocket endpoint at `/v1/sts/stream`
- Mock STT / LLM / TTS providers
- Optional OpenAI and Anthropic LLM adapters
- Provider routing with primary/fallback behavior
- In-memory session store with optional JSON persistence
- Basic keyword-based safety service
- Backend tests for API, WebSocket, provider routing, safety, and session storage

The next goal is to turn this backend skeleton into a runnable voice-demo MVP.

---

## Primary Objective

Build a local end-to-end Momoring demo where a user can:

1. Start a session
2. Send voice/audio input
3. Receive a transcript
4. Receive a Momoring text response
5. Hear a generated TTS audio response

The implementation should keep the existing provider abstraction and tests intact.

---

## Priority Order

### P0 — Preserve Existing Functionality

Before making changes:

- Inspect the current backend structure under `backend/`
- Keep existing public API contracts backward compatible unless a change is explicitly required
- Keep mock providers working for local/dev/test mode
- Ensure existing tests still pass

Done when:

```bash
cd backend
pytest -q
```

passes successfully.

---

### P1 — Add Real STT Provider

Current state: STT is mocked.

Goal: Add a real STT adapter while preserving the current `STTProvider` interface.

Implementation requirements:

- Add a real STT provider implementation under `backend/app/adapters/`
- Prefer OpenAI-compatible audio transcription if practical
- Make provider selection environment-driven
- Keep mock STT as the default when real credentials are unavailable
- Add reasonable timeout/error handling
- Normalize provider errors into safe fallback behavior

Suggested environment variables:

```env
USE_REAL_STT=false
OPENAI_API_KEY=
OPENAI_STT_MODEL=whisper-1
```

Expected behavior:

- If `USE_REAL_STT=true` and an API key is available, use the real STT provider
- Otherwise, use the mock STT provider

Tests to add/update:

- Provider factory returns mock STT by default
- Provider factory returns real STT when enabled and configured
- STT errors do not crash the WebSocket flow

Done when:

- Audio input can be converted to text through a real provider in local testing
- Mock mode still passes all tests

---

### P2 — Add Real TTS Provider

Current state: TTS is mocked and returns a fake `/audio/{session_id}/{uuid}.mp3` URL.

Goal: Add a real TTS adapter while preserving the current `TTSProvider` interface.

Implementation requirements:

- Add a real TTS provider implementation under `backend/app/adapters/`
- Make provider selection environment-driven
- Keep mock TTS as default when real credentials are unavailable
- Decide where generated audio should be stored locally
  - Recommended for MVP: `backend/.data/audio/`
- Add a static route or API route to serve generated audio files
- Ensure returned `audio_url` is playable by a browser client

Suggested environment variables:

```env
USE_REAL_TTS=false
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy
AUDIO_OUTPUT_DIR=.data/audio
```

Expected behavior:

- If `USE_REAL_TTS=true` and an API key is available, synthesize real audio
- Otherwise, return mock audio URLs as before

Tests to add/update:

- Mock TTS remains default
- Real TTS provider can be constructed when configured
- `/v1/tts/speak` returns a browser-playable URL or stable mock URL

Done when:

- A local client can play the TTS response audio
- Existing TTS endpoint behavior remains stable

---

### P3 — Improve WebSocket Audio Flow

Current state: WebSocket accepts `audio_chunk`, `end_of_utterance`, and unknown events.

Goal: Make WebSocket suitable for a real voice demo.

Implementation requirements:

- Continue supporting the existing message types:
  - `audio_chunk`
  - `end_of_utterance`
  - unknown event handling
- Use the configured STT provider for audio processing
- Support session-based turn storage
- Return events in a predictable order:
  1. `partial_transcript`
  2. `final_transcript`
  3. `bot_text`
  4. `tts_ready`
- Ensure malformed payloads return an error event instead of crashing
- Avoid blocking the whole server on provider errors

Recommended WebSocket event contract:

Client sends:

```json
{
  "type": "audio_chunk",
  "session_id": "...",
  "audio_base64": "..."
}
```

Client sends:

```json
{
  "type": "end_of_utterance",
  "session_id": "...",
  "text": "optional final text if already transcribed"
}
```

Server responds:

```json
{
  "type": "partial_transcript",
  "text": "..."
}
```

```json
{
  "type": "final_transcript",
  "text": "..."
}
```

```json
{
  "type": "bot_text",
  "text": "..."
}
```

```json
{
  "type": "tts_ready",
  "audio_url": "..."
}
```

Tests to add/update:

- Valid audio flow
- Provider error flow
- Missing session id
- Unknown event
- Malformed JSON/payload handling if feasible

Done when:

- WebSocket supports a complete voice interaction in mock mode and real-provider mode

---

### P4 — Add Minimal Frontend Demo

Current state: backend only.

Goal: Add a minimal browser demo for local validation.

Preferred implementation:

- Keep it simple
- Either add a minimal static HTML page served by FastAPI or create a small frontend folder
- For fastest MVP, use `backend/static/demo.html`

Demo requirements:

- Start session button
- Show session id
- Connect to WebSocket
- Record microphone audio or allow text fallback
- Send audio/text to the backend
- Display transcript
- Display Momoring response
- Play TTS audio

Recommended fallback behavior:

- If microphone handling is too much for the first pass, implement a text input fallback first
- The text fallback should still exercise `/v1/sts/session/start`, WebSocket or `/v1/sts/respond`, and `/v1/tts/speak`

Done when:

- A developer can run the backend and open a local page to test a full interaction

---

### P5 — Add `.env.example` and Developer Documentation

Goal: Make local setup clear for humans and Codex.

Add/update:

- `.env.example`
- `backend/README.md` or root `README.md`
- Document mock mode
- Document real provider mode
- Document test commands
- Document demo steps

Minimum `.env.example` should include:

```env
LLM_PRIMARY=gpt-5.4
LLM_FALLBACK=claude
FORCE_LLM_FALLBACK=false
SESSION_STORE_PATH=.data/sessions.json

USE_REAL_PROVIDERS=false
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4
OPENAI_BASE_URL=https://api.openai.com/v1

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4
ANTHROPIC_BASE_URL=https://api.anthropic.com/v1

USE_REAL_STT=false
OPENAI_STT_MODEL=whisper-1

USE_REAL_TTS=false
OPENAI_TTS_MODEL=gpt-4o-mini-tts
OPENAI_TTS_VOICE=alloy
AUDIO_OUTPUT_DIR=.data/audio
```

Done when:

- A new developer can clone, install, run, test, and try the demo using the docs

---

## Secondary Priorities

Do these after the local voice demo works.

### P6 — Replace JSON Session Storage with DB-backed Storage

Goal:

- Keep the current `SessionStore` behavior but support SQLite or PostgreSQL

Recommended path:

1. Add an abstract-ish store boundary if needed
2. Implement SQLite for local MVP
3. Keep JSON store as a simple fallback or test fixture
4. Add migration instructions only if necessary

Done when:

- Sessions, turns, and feedback survive server restarts through DB storage

---

### P7 — Add Session Token Validation

Current state: token is issued but not meaningfully enforced.

Goal:

- Protect session access with `session_id + token`

Implementation requirements:

- Store token when session is created
- Validate token for session detail, respond, feedback, and WebSocket
- Return `401` or WebSocket error/close for invalid tokens
- Keep tests clear and explicit

Done when:

- A request cannot access another session without a valid token

---

### P8 — Safety Improvements

Current state: basic banned keyword check.

Goal:

- Improve child-safety behavior for an education/voice companion product

Implementation ideas:

- Add input safety and output safety stages
- Add age-group-aware response rules
- Improve fallback messages
- Add tests for self-harm, violence, adult content, and unsafe advice categories
- Consider provider-based moderation later, but keep deterministic tests

Done when:

- Safety behavior is more robust and covered by tests

---

### P9 — Provider Reliability

Goal:

- Make provider routing production-friendlier

Implementation ideas:

- Timeout configuration
- Retry policy
- Error normalization
- Fallback logging
- Provider health metadata
- Tests for fallback-on-failure

Done when:

- Provider failure modes are predictable and tested

---

### P10 — Deployment Preparation

Goal:

- Make Momoring easy to run outside a local dev machine

Implementation ideas:

- Dockerfile
- docker-compose.yml
- CORS configuration
- Health check docs
- GitHub Actions CI
- Deployment README

Done when:

- `docker compose up` can run the MVP locally
- CI runs tests on PRs

---

## Recommended First Codex Task

Implement P1 through P5 in one PR if the change size is manageable.

If it becomes too large, split into these PRs:

1. `P1-P2`: Real STT/TTS providers and factory wiring
2. `P3`: WebSocket audio flow hardening
3. `P4-P5`: Local demo page and documentation

---

## Constraints

- Do not remove existing mock providers
- Do not break existing API tests
- Prefer small, explicit provider classes over large conditional logic in route handlers
- Keep real-provider network calls isolated in adapter classes
- Do not commit real API keys
- Keep test mode deterministic and offline-friendly
- Update tests alongside behavior changes

---

## Final Acceptance Checklist

Before marking the work complete:

```bash
cd backend
pytest -q
```

Also verify manually:

- Backend starts locally
- `/health` returns ok
- Session can be started
- STS respond works in mock mode
- TTS speak returns a usable audio URL or stable mock URL
- WebSocket flow completes without crashing
- Demo page can complete at least one interaction
- README or docs explain mock mode and real-provider mode
