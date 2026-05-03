# PR Inline Comment Resolution Plan (Execution)

## Scope
This plan converts unresolved inline comments into patch-sized tasks with explicit completion criteria.

## Phase 1 — Comment Triage and Mapping
For each unresolved review comment, capture:
- `comment_id` (or URL anchor)
- `file:path#line`
- `type` (`bug`, `contract`, `test`, `docs`)
- `required_change`
- `acceptance_test`

### Tracking Table
| Status | Comment | Area | Required patch | Acceptance |
|---|---|---|---|---|
| TODO | orchestrator tts shadowing risk | runtime bug | keep provider field separate from method name | `test_orchestrator_tts_method_uses_provider` |
| TODO | REST/WS error shape mismatch | API contract | enforce `error.code/message/trace_id` shape | `test_rest_session_not_found_error_shape`, WS error tests |
| TODO | session persistence corruption handling | persistence | backup corrupted JSON + atomic write | session_store corruption tests |
| TODO | output safety second-pass | safety | verify generated LLM output with safety policy | `test_orchestrator_blocks_unsafe_model_output` |

## Phase 2 — Patch-by-Comment Workflow
1. Pick one comment row.
2. Implement smallest code patch.
3. Add/fix one focused test.
4. Commit with message prefix:
   - `fix(comment:<id>): ...`
5. Mark row to `DONE` and attach commit hash.

## Phase 3 — Contract Lock
Lock these contract rules:
- REST errors: `{ "error": { "code", "message", "trace_id" } }`
- WS errors: `{ "type":"error", "error": { "code", "message", "trace_id" } }`
- `X-Trace-Id` header must equal `error.trace_id` for REST error responses.

## Phase 4 — Verification Gate
Run in order:
1. `cd backend && pytest -q`
2. `cd backend && python -m compileall app tests`

If dependency/network constraints block full test runs, record exact command + error and mark as environment warning.

## Phase 5 — Mergeability Recovery Checklist
- Rebase/merge from latest `main`.
- Resolve conflicts in order:
  1. `backend/app/main.py`
  2. `backend/app/services/*`
  3. `backend/tests/*`
- Re-run verification gate.
- Push and confirm PR mergeable state.
