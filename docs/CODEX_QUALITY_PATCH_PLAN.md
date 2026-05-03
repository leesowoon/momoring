# Codex Quality Patch Plan — Momoring Phase B-D

## Purpose

This plan captures the immediate quality, safety, and stability fixes discovered after reviewing the current Momoring backend code and QA documents.

The highest priority is to fix runtime stability and child-safety gaps before continuing with larger MVP feature work such as real STT/TTS integration, frontend demo, or PostgreSQL migration.

---

## Current Problems

### 1. QA documents and actual code state are out of sync

Some QA/traceability documents do not reflect the current implementation state.

Example:

- FR-07 appears to still say feedback persistence is not implemented.
- Current code already calls storage from `/v1/feedback`.

Impact:

- It is hard to determine what is complete, partially complete, or still missing.
- The team may duplicate work or miss real risks.

---

### 2. `SessionStore` load path is fragile

Current risk:

- Session persistence uses JSON file loading.
- If the JSON file is corrupted, malformed, or partially written, app startup can fail.
- Current loading logic does not appear to handle `json.loads(...)` failures robustly.

Impact:

- A single corrupted session file can prevent the backend from booting.
- This directly maps to an unfinished NFR item: corrupted session store recovery/failure handling.

---

### 3. Output safety filtering is missing

Current behavior:

- `STSOrchestrator.respond()` checks user input before calling the LLM.
- It does not appear to re-check the LLM-generated output.

Impact:

- Unsafe content can still be emitted if a model/provider returns unsafe text.
- For a child-facing voice service, output safety is required.

---

### 4. REST/WebSocket error contract is not standardized

Current behavior:

- WebSocket sends error strings such as `stt_failed`, `respond_failed`, or `tts_failed`.
- REST errors and WebSocket errors do not share a common schema.
- There is no consistent `trace_id`, `code`, and `message` contract.

Impact:

- Client-side handling becomes inconsistent.
- Debuggability and observability are weak.
- Trace/log standardization remains unfinished in NFR docs.

---

### 5. Real provider integration validation is still insufficient

Current behavior:

- Provider classes exist.
- Tests mainly cover mock mode and structural behavior.
- Real provider smoke/integration checks remain a future item.

Impact:

- Production/provider-mode failures may be discovered late.

---

### 6. Persistent storage is not production-ready

Current behavior:

- Session storage is JSON-file based.
- PostgreSQL migration is still only a plan.

Impact:

- Acceptable for MVP/local dev, but not enough for operational use.

---

## Execution Scope

Implement Phase B through Phase D first.

Phase A, E, and F should be handled after these code-level safety/stability patches or in a follow-up PR.

---

## Phase B — SessionStore Stability Patch

### Goal

Make session JSON persistence resilient against corrupted files and partial writes.

### Required changes

1. Update `SessionStore._load()` to handle corrupted or unreadable JSON files.

Expected behavior:

- If the persistence file is missing, continue with an empty store.
- If the file exists but is invalid JSON or has an unexpected structure:
  - Do not crash app startup.
  - Move/copy the bad file to a backup path ending in `.corrupt` or `.corrupt.<timestamp>`.
  - Start with an empty in-memory store.

2. Update persistence writes to be atomic.

Recommended approach:

- Write JSON to a temporary file in the same directory.
- Flush/write fully.
- Replace the destination file using an atomic replace operation.

3. Add focused tests.

Tests should cover:

- Missing file loads successfully.
- Valid JSON file loads successfully.
- Corrupted JSON file does not crash.
- Corrupted JSON file is backed up.
- Store starts empty after corrupted load.
- Persist writes produce readable JSON.

### Acceptance criteria

```bash
cd backend
pytest -q
```

passes, and a corrupted `.data/sessions.json` file does not prevent app startup.

---

## Phase C — Output Safety Patch

### Goal

Add a second safety check after LLM generation and before text is returned to REST or WebSocket clients.

### Required changes

1. Update `STSOrchestrator.respond()`.

Expected flow:

1. Check user input safety.
2. If unsafe, return safe fallback response with `blocked=True`.
3. Generate LLM response.
4. Check generated output safety.
5. If output is unsafe, return safe fallback response with `blocked=True`.
6. Otherwise return generated response with `blocked=False`.

2. Add tests for output blocking.

Recommended test approach:

- Use a fake or test LLM provider that returns text containing a banned keyword.
- Assert the orchestrator returns the safety fallback instead of the unsafe output.
- Assert `blocked=True`.

3. Preserve existing input safety behavior.

### Acceptance criteria

- Unsafe user input is blocked.
- Unsafe generated output is blocked.
- Safe input/output still works.
- Existing REST and WebSocket flows continue to work.

---

## Phase D — REST/WebSocket Error Contract and Trace ID

### Goal

Standardize backend error responses enough for client handling and debugging.

### Required changes

1. Add a shared error schema.

Suggested shape:

```json
{
  "error": {
    "code": "string_error_code",
    "message": "Human-readable message",
    "trace_id": "uuid-or-request-id"
  }
}
```

For WebSocket messages, preserve the event envelope:

```json
{
  "type": "error",
  "error": {
    "code": "stt_failed",
    "message": "Speech transcription failed.",
    "trace_id": "..."
  }
}
```

2. Add constants for error codes.

Suggested error codes:

- `invalid_payload`
- `session_not_found`
- `stt_failed`
- `respond_failed`
- `tts_failed`
- `unknown_event`
- `internal_error`

3. Add trace ID support.

Minimum viable approach:

- Generate a trace ID per REST request through middleware.
- Add it to response headers, for example `X-Trace-Id`.
- Use the same trace ID in standardized error payloads where practical.
- For WebSocket, generate one connection-level trace ID or per-error trace ID.

4. Add basic logging.

Minimum viable approach:

- Log error code and trace ID.
- Avoid logging secrets or full audio payloads.

5. Update tests.

Tests should cover:

- REST 404 session-not-found response includes standardized error shape if converted.
- WebSocket unknown event returns standardized error payload.
- WebSocket provider failure returns standardized error payload.
- `trace_id` exists in error payloads.

### Acceptance criteria

- Client receives a consistent `code`, `message`, and `trace_id` for handled errors.
- Existing success API contracts remain backward compatible where possible.
- Tests pass.

---

## Follow-up Phase A — QA/Traceability Document Sync

After code patches or in a separate docs PR:

1. Update `fr_traceability_matrix.md` to match current implementation.
2. Fix FR-07 status:
   - feedback API is implemented
   - storage behavior exists
   - verification status should be separated from implementation status
3. Clarify FR-01/FR-03 mock vs real provider status.
4. Add a Definition of Done column or equivalent fields:
   - `Implemented`
   - `Tested`
   - `Verified manually`
   - `Production-ready`

Acceptance criteria:

- Docs clearly distinguish implementation completion from verification and production readiness.

---

## Follow-up Phase E — Verification Strengthening

After Phase B-D:

1. Add real-provider smoke tests gated by environment variables.
2. Keep smoke tests skipped by default when keys are absent.
3. Add NFR check scripts where practical:
   - P95 latency smoke
   - provider fallback smoke
   - safety batch checks
4. Add or update Go/No-Go checklist.

Acceptance criteria:

- CI remains offline-friendly.
- Staging/provider checks can be run explicitly when credentials are configured.

---

## Follow-up Phase F — Operational Storage

Next sprint:

1. Keep the `SessionStore` API boundary stable.
2. Add PostgreSQL-backed repository/store.
3. Prepare migration and rollback notes.
4. Rehearse JSON-to-DB migration path.

Acceptance criteria:

- Storage can move from local JSON to operational DB without rewriting route handlers.

---

## Recommended First PR

Title:

`Stabilize session persistence, output safety, and error contracts`

Scope:

- Phase B
- Phase C
- Phase D
- Tests for each change

Do not include:

- PostgreSQL migration
- Real provider smoke tests that require credentials by default
- Large frontend changes
- Large QA doc rewrite unless trivial

---

## Final Checklist

Before marking the PR complete:

```bash
cd backend
pytest -q
```

Manual checks:

- Backend starts with no session file.
- Backend starts with a valid session file.
- Backend starts with a corrupted session file and backs it up.
- Unsafe user input is blocked.
- Unsafe LLM output is blocked.
- WebSocket unknown event returns standardized error payload.
- No real secrets are logged or committed.
