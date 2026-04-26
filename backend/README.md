# Momoring MVP Backend (FastAPI)

## Run
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Test
```bash
pytest -q
```

## Current Implementation
- Adapter 구조(`app/adapters`): STT/LLM/TTS provider interface + mock 구현
- Service 구조(`app/services`): SafetyService, STSOrchestrator
- API 레이어(`app/main.py`): REST + WebSocket endpoint

## Added in Next Step
- `GET /v1/sts/session/{session_id}`: 세션/턴 조회 (in-memory)
- `SessionStore`: 세션 생성/턴 기록/조회

## Provider Routing (GPT-5.4 / Claude)
- 기본: GPT-5.4 mock provider
- fallback: Claude mock provider
- 환경변수
  - `LLM_PRIMARY` (default: `gpt-5.4`)
  - `LLM_FALLBACK` (default: `claude`)
  - `FORCE_LLM_FALLBACK=true` 로 fallback 강제
- 확인 API: `GET /v1/meta/provider`

## Session Persistence
- 기본 경로: `.data/sessions.json`
- 환경변수 `SESSION_STORE_PATH`로 저장 경로 변경 가능

## Real Provider Mode (Optional)
- `USE_REAL_PROVIDERS=true` 설정 시 API key가 있으면 실 provider adapter 사용
- OpenAI
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (default: `gpt-5.4`)
  - `OPENAI_BASE_URL` (default: `https://api.openai.com/v1`)
- Anthropic
  - `ANTHROPIC_API_KEY`
  - `ANTHROPIC_MODEL` (default: `claude-sonnet-4`)
  - `ANTHROPIC_BASE_URL` (default: `https://api.anthropic.com/v1`)

## WebSocket Test Coverage
- `backend/tests/test_ws_flow.py` 에서 `audio_chunk`, `end_of_utterance`, `unknown` 이벤트 계약 검증

