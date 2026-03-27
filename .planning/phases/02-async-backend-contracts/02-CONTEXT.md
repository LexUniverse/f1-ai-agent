# Phase 2: Async Backend Contracts - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Define and implement stable asynchronous API contracts for `/start_chat`, `/message_status`, and `/next_message` with strict typed schemas, deterministic session semantics, and consistent error handling.

</domain>

<decisions>
## Implementation Decisions

### Session API Contract
- **D-01:** `session_id` format is UUIDv4 (string representation).
- **D-02:** Session error status mapping is strict:
  - `404` when session does not exist,
  - `401` when session exists but is not authorized,
  - `410` when session is expired.
- **D-03:** `/start_chat` remains single session bootstrap entrypoint and returns session handle only after successful auth flow.

### Message Status Lifecycle
- **D-04:** Status state machine is `queued -> processing -> ready | failed`.
- **D-05:** `/message_status` is polling-safe and must return current state without mutating business outcome.
- **D-06:** `failed` status must include machine-readable failure code in error envelope.

### Error Envelope
- **D-07:** All API errors use unified envelope:
  - `{ "error": { "code": "...", "message": "...", "details": {...} } }`
- **D-08:** Existing auth errors from Phase 1 must be adapted to unified envelope while preserving stable machine codes.
- **D-09:** Validation errors (schema/input) should be normalized into the same envelope shape.

### Claude's Discretion
- Exact TTL duration and expiration source (absolute timeout vs inactivity timeout) for session lifecycle.
- Internal message task storage model for v1 async simulation (in-memory with clear upgrade path).
- Concrete `details` payload keys per error code, as long as envelope contract remains stable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Core scope and requirement anchors
- `.planning/ROADMAP.md` — Phase 2 goal, requirement mapping (`API-01..API-04`), and success criteria.
- `.planning/REQUIREMENTS.md` — backend/API contract requirements and current traceability.
- `.planning/PROJECT.md` — quality constraints (accuracy, latency, RU-first UX, trust-first behavior).

### Prior phase artifacts (must remain compatible)
- `.planning/phases/01-access-control/01-CONTEXT.md` — locked auth/session behavior from Phase 1.
- `.planning/phases/01-access-control/01-VERIFICATION.md` — verified auth assumptions that Phase 2 must preserve.
- `.planning/phases/01-access-control/01-01-SUMMARY.md` — auth primitives and limiter/session foundation.
- `.planning/phases/01-access-control/01-02-SUMMARY.md` — endpoint auth gate integration details.

### Research context
- `.planning/research/ARCHITECTURE.md` — deterministic orchestration and contract-first service boundaries.
- `.planning/research/PITFALLS.md` — failure-mode and trust signaling guidance.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/api/chat.py` currently hosts all three target endpoints and auth gate integration points.
- `src/auth/dependencies.py` provides reusable pre-handler authorization guard.
- `src/sessions/store.py` provides session state object and in-memory store foundation.
- `src/models/auth.py` and `src/auth/errors.py` already provide typed auth error primitives.

### Established Patterns
- Deterministic pre-handler auth checks are already validated and must be preserved.
- Phase 1 uses test-first verification (`tests/test_auth.py`) with clear machine-code assertions.
- Current backend is minimal and in-memory; phase 2 should formalize contracts without premature infra complexity.

### Integration Points
- `/start_chat` response contract and session creation path in `src/api/chat.py`.
- `/message_status` and `/next_message` handler responses in `src/api/chat.py`.
- Error model normalization point in `src/auth/errors.py` and shared response models module to be introduced in Phase 2.

</code_context>

<specifics>
## Specific Ideas

- User explicitly locked:
  - UUIDv4 session IDs,
  - status lifecycle `queued -> processing -> ready | failed`,
  - unified `error` envelope for all API failures.
- Other phase 2 details delegated to Claude with safe defaults.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-async-backend-contracts*
*Context gathered: 2026-03-27*
