# FR/NFR 추적표 (Traceability Matrix)

| ID | 요구사항 요약 | 현재 구현 상태 | 근거 파일 | 테스트 상태 | 우선순위 |
|---|---|---|---|---|---|
| FR-01 | STT 입력/발화 종료 감지 | 부분구현(mock 기반) | `backend/app/main.py` WS | 미흡(WS E2E 필요) | P1 |
| FR-02 | 대화 오케스트레이션 | 구현 | `backend/app/services/orchestrator.py` | 부분(추가 필요) | P0 |
| FR-03 | TTS 출력 | 부분구현(mock) | `backend/app/main.py`, `adapters/mock.py` | 부분 | P1 |
| FR-04 | 캐릭터 상태 연동 | 백엔드 범위 외(프론트 미구현) | N/A | N/A | P2 |
| FR-05 | 입력/출력 안전 필터 | 구현(키워드 룰) | `backend/app/services/safety.py` | 부분(회귀 강화 필요) | P0 |
| FR-06 | 로그/모니터링 | 부분구현(세션 저장) | `backend/app/services/session_store.py` | 부분 | P1 |
| FR-07 | 피드백 수집 | 구현(저장 로직 미구현) | `backend/app/main.py` | 미흡 | P1 |
| NFR-01 | P95 지연시간 2.5s | 미검증 | 측정 스크립트 없음 | 미흡 | P1 |
| NFR-02 | 장애 fallback | 부분구현(router fallback) | `provider_router.py` | 부분 | P1 |
| NFR-03 | 보안/개인정보 | 부분구현(정책만) | docs 중심 | 미흡 | P2 |
| NFR-04 | 안전성 지표 | 미검증 | 지표 측정 부재 | 미흡 | P1 |

## 즉시 액션
1. API E2E 테스트로 FR-02/05/07 검증 강화
2. WS 계약 테스트로 FR-01 커버
3. NFR 측정 체크리스트 작성
