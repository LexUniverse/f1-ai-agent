# Phase 1: Access Control - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Restrict assistant usage to users with valid personal allowlist access codes. Unauthorized users must be blocked before any downstream chat processing.

</domain>

<decisions>
## Implementation Decisions

### Authentication Checkpoint
- **D-01:** Validate access code at session start (`/start_chat`) and bind authorization to the created session.
- **D-02:** Re-validate on message endpoints only by checking session auth state (no repeated code prompt per message).

### Allowlist Storage and Operations
- **D-03:** Store allowlist in environment variable `AUTH_ALLOWLIST_CODES` as comma-separated codes for v1 simplicity.
- **D-04:** Normalize input and stored codes (trim whitespace, exact case-sensitive match by default).
- **D-05:** Keep operational model manual in v1 (deploy-time updates to allowlist, no admin UI yet).

### Unauthorized Behavior and Safety
- **D-06:** Return explicit unauthorized response with stable machine-readable code (e.g., `AUTH_INVALID_CODE`) and user-facing Russian message.
- **D-07:** Add lightweight brute-force guardrail: per-IP/per-session failed-attempt counter with temporary cooldown.
- **D-08:** Log auth failures with masked code values only (never full code in logs).

### Session Lifetime
- **D-09:** Authorization lifetime is one chat session; user enters code once per new session.
- **D-10:** Session-bound auth must be invalid after session expiration/termination.

### Claude's Discretion
- Cooldown duration and threshold defaults.
- Exact HTTP status mapping for each auth error case.
- Session storage mechanism details (in-memory vs pluggable backend) consistent with Phase 2 API contracts.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase and requirements anchors
- `.planning/ROADMAP.md` — Phase 1 goal, dependency boundaries, success criteria for access control.
- `.planning/REQUIREMENTS.md` — `AUTH-01` and `AUTH-02` requirement definitions and traceability constraints.
- `.planning/PROJECT.md` — Core value and constraint context (trust, accuracy, RU-first UX).

### Research guidance for risk controls
- `.planning/research/PITFALLS.md` — reliability and failure-handling patterns relevant to trust and safe degraded behavior.
- `.planning/research/ARCHITECTURE.md` — recommended component boundaries and deterministic control-flow principles.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No application source code exists yet; this phase should establish initial auth module and API integration points.

### Established Patterns
- Planning artifacts enforce deterministic behavior and explicit failure messaging.
- Requirement IDs and phase traceability are already standardized in `.planning/REQUIREMENTS.md`.

### Integration Points
- Session creation flow at `/start_chat` (Phase 2 contract) is the primary auth gate.
- Session state check should be reusable by `/message_status` and `/next_message`.

</code_context>

<specifics>
## Specific Ideas

- User locked one explicit preference: authorization is entered once per session.
- Remaining access-control details were delegated to Claude with a secure-default approach.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-access-control*
*Context gathered: 2026-03-26*
