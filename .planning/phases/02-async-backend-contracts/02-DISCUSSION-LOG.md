# Phase 2: Async Backend Contracts - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 02-async-backend-contracts
**Areas discussed:** Session API contract, status lifecycle, error envelope

---

## Session API contract

| Option | Description | Selected |
|--------|-------------|----------|
| UUIDv4 + strict status mapping | `404` missing, `401` unauthorized, `410` expired | ✓ |
| Opaque session + simplified auth errors | All session problems mapped to `401` | |

**User's choice:** UUIDv4 with strict 404/401/410 semantics.
**Notes:** Session ID and failure mapping are locked for this phase.

---

## Message status lifecycle

| Option | Description | Selected |
|--------|-------------|----------|
| Full async lifecycle | `queued -> processing -> ready | failed` | ✓ |
| Reduced lifecycle | `processing | ready | failed` | |

**User's choice:** Full lifecycle with explicit queue state.
**Notes:** Polling contract should expose intermediate queue stage.

---

## Error envelope standard

| Option | Description | Selected |
|--------|-------------|----------|
| Unified envelope | `{ "error": { "code", "message", "details" } }` across all endpoints | ✓ |
| Native framework envelope | Keep heterogeneous `detail` responses | |

**User's choice:** Unified error envelope.
**Notes:** Existing auth errors should be normalized without losing machine codes.

---

## Claude's Discretion

- Session TTL internals.
- In-memory async task state implementation details.
- Concrete `details` keys per error type.

## Deferred Ideas

None.
