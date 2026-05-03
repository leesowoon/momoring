# Momoring MVP QA 우선순위 리스트 (실행용)

## P0 (즉시)
1. **요구사항 추적표(FR/NFR Traceability) 완성**
   - 산출물: `qa/fr_traceability_matrix.md`
   - 목표: 기능 구현/미구현 상태를 객관화
2. **핵심 API E2E 테스트 추가**
   - 산출물: `backend/tests/test_api_flow.py`
   - 목표: `start -> respond -> session detail` 흐름 검증
3. **안전 응답 회귀 테스트 강화**
   - 산출물: `backend/tests/test_api_flow.py`
   - 목표: 금지어 입력 시 blocked 및 fallback 응답 보장

## P1 (이번 스프린트)
4. **WS 이벤트 계약 테스트 추가**
   - 산출물: `backend/tests/test_ws_flow.py`
5. **NFR 측정 스크립트 초안**
   - 산출물: `qa/nfr_checklist.md`

## P2 (다음 스프린트)
6. **실 provider 연동 통합 테스트(스테이징 전용)**
7. **PostgreSQL 저장소 전환 설계/마이그레이션 계획**

---

## 자동 진행 기록
- [x] P0-1 시작: FR/NFR 추적표 생성
- [x] P0-2 시작: API E2E 테스트 파일 추가
- [x] P0-3 시작: 안전 회귀 케이스 포함


## P0.5 (리뷰 코멘트 해소 트랙)
8. **Inline comment 해소 플로우 실행**
   - 산출물: `qa/inline_comment_resolution_plan.md`
   - 목표: 코멘트별 수정/테스트/커밋 매핑 고정
9. **에러 계약 Lock 검증**
   - 산출물: `backend/tests/test_api.py`, `backend/tests/test_ws_flow.py`
   - 목표: REST/WS error schema 일관성 유지
