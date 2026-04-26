# Momoring MVP 기술 설계서 (Framework & Architecture)

## 1. 기술 결정 (MVP 고정안)

## 1.1 Frontend
- Framework: **Next.js 15 (React + TypeScript)**
- UI: Tailwind CSS
- Audio 처리: Web Audio API + MediaRecorder
- 상태관리: Zustand
- 실시간 통신: WebSocket(음성 스트리밍), HTTP(제어/API)

## 1.2 Backend
- Framework: **FastAPI (Python 3.12)**
- 비동기 런타임: Uvicorn + asyncio
- API 스타일: REST + WebSocket
- 인증: JWT (보호자/운영자 콘솔용), MVP 사용자 익명 세션 토큰

## 1.3 AI/음성 계층
- STT Adapter: provider-agnostic 인터페이스 (`STTProvider`)
- LLM Orchestrator: 연령 정책 + 안전 정책 + 시스템 프롬프트 조합
- TTS Adapter: provider-agnostic 인터페이스 (`TTSProvider`)
- Safety Engine: 입력 필터 + 출력 필터 + 위험 응답 템플릿

## 1.4 데이터/인프라
- DB: PostgreSQL 16
- Cache/Queue: Redis 7
- Object Storage: S3 호환 스토리지(오디오 임시 저장)
- Observability: OpenTelemetry + Prometheus + Grafana
- 배포: Docker + (선택) Kubernetes
- CI/CD: GitHub Actions

---

## 2. 시스템 아키텍처

```text
[Client: Next.js]
  ├─ Audio Capture (Web Audio API)
  ├─ Character Renderer (state machine + lipsync)
  └─ WS/HTTP Client
        |
        v
[API Gateway / FastAPI]
  ├─ Session Service
  ├─ STS Orchestrator
  │    ├─ STT Adapter
  │    ├─ Prompt Builder (age + persona + safety)
  │    ├─ LLM Adapter
  │    └─ TTS Adapter
  ├─ Safety Service
  ├─ Feedback Service
  └─ Metrics/Logging Service
        |
        +--> PostgreSQL
        +--> Redis
        +--> Object Storage
        +--> Monitoring Stack
```

---

## 3. 서비스 경계 및 모듈 구조

## 3.1 Backend 모듈
- `app/api/` : REST/WS 엔드포인트
- `app/services/session_service.py`
- `app/services/sts_orchestrator.py`
- `app/services/safety_service.py`
- `app/adapters/stt/`
- `app/adapters/llm/`
- `app/adapters/tts/`
- `app/repositories/` : DB 접근
- `app/schemas/` : Pydantic DTO

## 3.2 Frontend 모듈
- `src/features/sts/` : 음성 캡처/송신
- `src/features/character/` : 상태머신/애니메이션/립싱크
- `src/features/chat/` : 대화 로그/피드백 UI
- `src/lib/api/` : API 클라이언트
- `src/stores/` : 전역 상태

---

## 4. 핵심 시퀀스 (런타임 흐름)

1. 클라이언트가 세션 생성 (`POST /v1/sts/session/start`)
2. 사용자 발화 오디오를 WS로 chunk 송신
3. 서버 STT Adapter가 partial/final transcript 생성
4. final transcript를 Safety Service 입력 필터로 검사
5. LLM Orchestrator가 연령/페르소나/안전 정책 결합 후 응답 생성
6. 출력 텍스트를 Safety Service로 재검사
7. 통과 시 TTS Adapter로 음성 생성
8. 클라이언트로 오디오 스트림/URL 반환
9. 캐릭터는 speaking 상태로 전환 후 립싱크 실행
10. 턴 로그/지연시간/안전 이벤트 저장

---

## 5. API 계약 (상세)

## 5.1 `POST /v1/sts/session/start`
- Request: `{ "age_group": "7-9" | "10-12" | "13-15" }`
- Response: `{ "session_id": "...", "ws_url": "...", "token": "..." }`

## 5.2 `WS /v1/sts/stream`
- Client Message
  - `{ "type":"audio_chunk", "session_id":"...", "seq":1, "audio_base64":"..." }`
  - `{ "type":"end_of_utterance", "session_id":"..." }`
- Server Message
  - `{ "type":"partial_transcript", "text":"..." }`
  - `{ "type":"final_transcript", "text":"..." }`
  - `{ "type":"bot_text", "text":"..." }`
  - `{ "type":"tts_ready", "audio_url":"..." }`
  - `{ "type":"safety_block", "reason":"...", "safe_text":"..." }`

## 5.3 `POST /v1/feedback`
- Request: `{ "session_id":"...", "turn_id":"...", "rating":"up|down", "reason":"..." }`
- Response: `{ "ok": true }`

---

## 6. 데이터 스키마 (MVP)

## 6.1 sessions
- `id` (uuid, pk)
- `age_group` (varchar)
- `started_at` (timestamp)
- `ended_at` (timestamp, nullable)
- `status` (active|closed|error)

## 6.2 turns
- `id` (uuid, pk)
- `session_id` (fk)
- `user_text` (text)
- `bot_text` (text)
- `latency_ms` (int)
- `safety_flag` (boolean)
- `created_at` (timestamp)

## 6.3 safety_events
- `id` (uuid, pk)
- `session_id` (fk)
- `event_type` (input_block|output_block|high_risk)
- `severity` (low|medium|high)
- `detail` (jsonb)
- `created_at` (timestamp)

---

## 7. 성능/안전 SLO
- P95 응답 지연: <= 2500ms
- 세션 실패율: < 3%
- 유해 응답 미노출률: >= 99.5%
- 고위험 발화 감지 재현율: >= 95%

---

## 8. 배포 아키텍처
- `web` (Next.js)
- `api` (FastAPI)
- `worker` (비동기 배치/후처리)
- `postgres`, `redis`
- `otel-collector`, `prometheus`, `grafana`

환경 분리:
- `dev` / `staging` / `prod`

---

## 9. MVP 이후 확장 포인트
- STT/TTS provider 교체(어댑터 유지)
- 다국어/다캐릭터 확장
- 개인화 메모리 계층 추가
- 보호자 대시보드 고도화

---

## 10. 인증/권한/보안 설계

### 10.1 인증 모델
- 사용자 앱 세션: 단기 익명 세션 토큰(기기 고유 식별자와 분리)
- 보호자/운영자 콘솔: JWT + Refresh Token
- 내부 서비스 호출: 서비스 간 API Key 또는 mTLS(환경별 선택)

### 10.2 권한 모델(RBAC)
- `viewer`: 모니터링 읽기
- `operator`: 안전 이벤트 처리/운영 액션
- `admin`: 정책 수정/권한 관리

### 10.3 전송/저장 보안
- 모든 외부 트래픽 TLS 1.2+
- 민감 로그 필드 마스킹(전화/이메일/주소 추정 문자열)
- DB at-rest 암호화, 백업 암호화

### 10.4 개인정보 최소화 규칙
- 원본 오디오 장기보관 금지(MVP 기본: 미보관)
- 텍스트 로그 보관기간 기본 30일, 안전 이벤트 90일
- 삭제 요청 시 세션 단위 soft-delete 후 배치 purge

---

## 11. 신뢰성/장애 대응 설계

### 11.1 장애 유형
1. STT provider 지연/오류
2. LLM provider 지연/타임아웃
3. TTS provider 실패
4. Redis/Postgres 연결 오류

### 11.2 공통 장애 처리
- timeout: STT 4s / LLM 6s / TTS 4s (초기값)
- retry: idempotent 요청에 한해 최대 2회(지수 백오프)
- circuit breaker: provider별 실패율 임계치 초과 시 60초 차단
- fallback: 텍스트 기반 안전 응답 또는 짧은 고정 안내 음성

### 11.3 세션 복구 전략
- WS 끊김 시 10초 이내 재접속 허용
- `session_id` + `last_seq`로 이어받기
- 복구 실패 시 세션 종료 이벤트 기록 후 새 세션 유도

---

## 12. STS 상태 머신 상세

### 12.1 클라이언트 상태
- `idle`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `error`

### 12.2 상태 전이 규칙
- `idle -> listening`: 사용자가 마이크 시작
- `listening -> transcribing`: chunk 수신 시작
- `transcribing -> thinking`: 발화 종료 감지
- `thinking -> speaking`: bot_text + tts_ready 수신
- `speaking -> listening`: barge-in 감지
- `* -> error`: 치명 오류 발생

### 12.3 상태 기반 UI 제약
- `speaking` 중 입력 버튼은 "끼어들기" 버튼으로 변경
- `error` 상태에서 재시도 버튼/오프라인 안내 제공

---

## 13. 프롬프트/정책 계층 설계

### 13.1 Prompt 빌더 계층
1. 시스템 공통 프롬프트(페르소나/톤)
2. 연령대 프롬프트(7-9, 10-12, 13-15)
3. 안전 정책 프롬프트(금지/완화/대체응답)
4. 세션 컨텍스트(최근 N턴)

### 13.2 토큰 예산 정책
- 입력 컨텍스트 상한: 2,000 tokens
- 최근 대화 N턴 유지: 기본 8턴
- 초과 시 요약 메모리로 압축

### 13.3 안전 응답 우선순위
- 고위험 감지 시 LLM 생성 응답보다 안전 템플릿 우선
- "설명 거부 + 안전한 대안 + 도움 요청 권고" 3단 구성

---

## 14. 데이터 보존/관측 가능성

### 14.1 로그 스키마 (필수 필드)
- `trace_id`, `session_id`, `turn_id`, `age_group`
- `stt_ms`, `llm_ms`, `tts_ms`, `total_ms`
- `safety_input`, `safety_output`, `error_code`

### 14.2 메트릭 정의
- Counter: `sessions_started_total`, `sessions_failed_total`
- Histogram: `sts_latency_ms`, `stt_latency_ms`, `llm_latency_ms`, `tts_latency_ms`
- Gauge: `active_sessions`
- Counter: `safety_block_total{type=input|output|high_risk}`

### 14.3 알람 규칙(초기)
- P95 latency > 2500ms, 10분 지속
- session failure rate > 3%, 15분 지속
- high_risk 이벤트 급증(평균 대비 2배)

---

## 15. 확장성/성능 용량 계획

### 15.1 MVP 목표 트래픽
- 동시 세션: 100
- 분당 신규 세션: 30
- 평균 턴 길이: 10초

### 15.2 스케일링 전략
- API pod: CPU 사용률 60% 기준 HPA
- Worker pod: queue depth 기준 HPA
- Redis/Postgres: managed 서비스 사용 권장

### 15.3 성능 최적화 항목
- 오디오 코덱 압축(예: opus)
- partial transcript UI 즉시 반영
- TTS 캐시(동일 안전 안내문)

---

## 16. 테스트 전략 (MVP)

### 16.1 자동화 테스트
- 단위 테스트
  - Prompt 빌더
  - Safety policy 매처
  - 상태머신 전이
- 통합 테스트
  - STT mock -> LLM mock -> TTS mock 파이프라인
- 계약 테스트
  - WS 메시지 스키마
  - REST API request/response

### 16.2 시나리오 테스트
- 정상 대화 20개
- 발화 중단/재시작 10개
- 고위험 시나리오 30개
- provider timeout/오류 20개

### 16.3 품질 게이트
- 핵심 유즈케이스 pass rate >= 95%
- high severity 버그 0개

---

## 17. 배포/릴리즈 절차

### 17.1 브랜치/환경
- `main` -> staging 자동 배포
- 수동 승인 후 production 배포

### 17.2 릴리즈 체크리스트
- DB migration 검증
- API 호환성 검증
- 관측 대시보드/알람 확인
- 롤백 이미지 태그 준비

### 17.3 롤백 전략
- Blue/Green 또는 Canary 배포
- 문제 시 이전 이미지로 5분 내 복귀 목표

---

## 18. 오픈 이슈 (의사결정 필요)
1. GPT-5.4/Claude 최종 우선순위 확정(품질/지연/비용 비교)
2. 오디오 원본 미보관 원칙의 예외 허용 여부
3. 보호자 콘솔 MVP 포함 범위
4. 모바일 앱 우선 vs 웹 우선 출시 전략

---

## 19. AI 모델/프로바이더 선정안 (MVP)

## 19.1 선정 원칙
- 아동 대상 안전성(정책 제어 가능)
- 한국어 대화 품질
- 실시간 지연 성능
- 비용 대비 품질
- 장애 시 대체 경로 제공 가능

## 19.2 MVP 1차 선정(권장)
### LLM
- Primary 후보 A: `GPT-5.4` 계열(사용 가능 시 최우선)
- Primary 후보 B: `Claude` 최신 상용 계열(벤치마크 동률/우위 시 채택)
- Fallback: 저비용/저지연 보조 모델(장애·예산 초과 시)

### STT
- Primary: 고정밀 상용 STT(한국어 성능 기준 통과 필수)
- Fallback: Whisper 계열 self-hosted 또는 2nd vendor STT

### TTS
- Primary: 아동 친화 음색 지원 상용 TTS
- Fallback: vendor B TTS(고정 안전 안내문 우선 재생)

> 주의: 실제 모델명/버전은 가용성, 계약 조건, 비용, 지연 벤치마크 결과로 확정한다.

## 19.3 모델 라우팅 정책
- 일반 대화: GPT-5.4 우선 라우팅(가용 시)
- GPT-5.4 미가용/지연 초과: Claude로 자동 전환
- 고위험 대화: 안전 템플릿 응답 우선(모델 출력 무시 가능)
- provider 장애: fallback 모델로 자동 전환
- 월 예산 임계치 초과: 저비용 모델로 단계적 다운시프트

## 19.4 벤치마크 및 확정 절차
- 평가 기간: 5영업일
- 평가 항목
  1) 한국어 대화 자연성
  2) 연령 맞춤 설명 정확도
  3) 안전 응답 일관성
  4) P95 지연시간
  5) 1,000턴당 비용
- 확정 기준: 품질 점수 40% + 안전 점수 30% + 지연 20% + 비용 10%

## 19.5 운영 시 모델 버전 관리
- 모델 변경은 feature flag로 점진 적용(5% -> 25% -> 100%)
- 변경 전/후 A/B 리포트 필수
- 회귀 발생 시 즉시 롤백

