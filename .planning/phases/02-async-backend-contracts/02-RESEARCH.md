# Phase 2: Async Backend Contracts - Research

**Researched:** 2026-03-27
**Domain:** FastAPI async contract design and typed API schema enforcement
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-01 | Client can start a session via async endpoint equivalent to `/start_chat`. | Typed `StartChatRequest/Response`, UUIDv4 generation at store boundary, auth-first bootstrap sequencing. |
| API-02 | Client can poll status via async endpoint equivalent to `/message_status`. | Explicit status state model and polling-safe read semantics (`GET` returns current state, no business mutation). |
| API-03 | Client can request next response via async endpoint equivalent to `/next_message`. | Contracted response model for next message and deterministic consumption semantics tied to session/message handle. |
| API-04 | API validates structured input/output contracts via Pydantic models. | Pydantic request/response models, response filtering via `response_model`, and normalized validation error envelope. |
</phase_requirements>

## Summary

Phase 2 should formalize the existing endpoint skeleton in `src/api/chat.py` into stable asynchronous contracts rather than changing product behavior. The current code already has endpoint paths and auth-gating hooks, but status and next-message contracts are still placeholders (`status="ready"` and fixed `"response"`), and error payloads are currently in FastAPI `detail` shape from Phase 1.

The planning focus should be on introducing explicit typed models for session, status, next-message, and unified error envelopes while preserving all locked Phase 1 auth behavior. Design should keep in-memory storage for v1 (consistent with current `SessionStore`) and encode a deterministic state machine (`queued -> processing -> ready | failed`) with session-expiry semantics.

**Primary recommendation:** Implement a contract-first API layer in FastAPI using strict Pydantic models and centralized exception handlers that normalize all errors (auth + validation + domain) into the locked envelope shape.

## Project Constraints (from .cursor/rules/)

No `.cursor/rules/` directory exists in this repository; no additional project-specific rule directives were found.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.14.0 (local runtime) | Backend runtime | Current local interpreter; supports modern typing used across codebase. |
| FastAPI | 0.135.2 (installed) | HTTP routing, dependency injection, exception handling, OpenAPI | Native fit for typed request/response contracts and dependency-based auth gates. |
| Pydantic | 2.12.5 (installed) | Request/response schema validation and serialization | FastAPI-native validation and schema generation backbone. |
| Uvicorn | 0.42.0 (installed) | ASGI server | Default FastAPI serving path for local/dev execution. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 (installed) | Contract and behavior regression tests | Unit/integration checks for endpoint contracts and error envelopes. |
| stdlib `uuid` | Python 3.14 stdlib | UUIDv4 generation/validation | Enforce locked `session_id` UUIDv4 format. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| In-memory async task/session maps | Redis + worker queue | Better durability/scaling, but adds infra complexity beyond Phase 2 scope. |
| Local exception normalization in each endpoint | Global exception handlers | Global handlers reduce drift and guarantee envelope consistency. |

**Installation (if dependencies are missing):**
```bash
python3 -m pip install fastapi uvicorn pydantic pytest
```

**Version verification:** Versions above were verified against the active local environment (`python3 --version`, `pytest --version`, and module version introspection). No `pyproject.toml`/`requirements.txt` lockfile is present in the repo, so planner should include explicit dependency pinning as a follow-up hardening task.

## Architecture Patterns

### Recommended Project Structure
```
src/
├── api/                # Endpoint handlers and route wiring
├── models/             # Request/response/error contract models
├── auth/               # Auth dependencies, decisions, and auth-domain errors
└── sessions/           # Session/message state and lifecycle management
```

### Pattern 1: Contract-First Endpoints
**What:** Every endpoint uses explicit Pydantic request/response models, never untyped dict payloads.
**When to use:** All public API handlers in this phase.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/response-model/
@router.post("/start_chat", response_model=StartChatResponse)
def start_chat(payload: StartChatRequest, request: Request):
    ...
```

### Pattern 2: Dependency-Gated Session Access
**What:** Keep auth/session authorization in FastAPI dependencies so unauthorized requests fail before business logic runs.
**When to use:** `message_status` and `next_message`.
**Example:**
```python
def _session_dependency(request: Request, x_session_id: str | None = Header(default=None)):
    store: SessionStore = request.app.state.session_store
    return require_authorized_session(x_session_id=x_session_id, store=store)
```

### Pattern 3: Centralized Error Envelope Normalization
**What:** Use FastAPI exception handlers to normalize `HTTPException` and `RequestValidationError` into `{ "error": { ... } }`.
**When to use:** App-level setup in `src/main.py`.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/handling-errors/
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": {...}})
```

### Anti-Patterns to Avoid
- **Endpoint-local envelope formatting:** causes drift between auth/validation/domain errors.
- **Mutating state in status polling:** violates locked polling-safe semantics.
- **Untyped status strings:** makes client state handling fragile; use constrained enums/literals.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Request/response schema validation | Custom JSON validation | Pydantic models in FastAPI signatures | Built-in validation, coercion, schema docs, and precise error locations. |
| API error interception | Manual try/except per endpoint | FastAPI exception handlers | Centralized behavior and consistent envelope output. |
| UUID formatting/parsing | Regex-only UUID validation | `uuid.UUID(...)` and `uuid4()` | Avoid subtle format/version mismatches and parsing bugs. |
| Contract testing harness | Custom HTTP test harness | `fastapi.testclient` + pytest | Existing project test pattern already uses this stack. |

**Key insight:** Phase 2 risk is contract inconsistency, not algorithmic complexity; standard FastAPI/Pydantic primitives already solve most consistency problems.

## Common Pitfalls

### Pitfall 1: FastAPI default validation payload leaks into API contract
**What goes wrong:** Validation errors return default `{detail: [...]}` instead of required `{error:{...}}`.
**Why it happens:** `RequestValidationError` handler not overridden globally.
**How to avoid:** Register app-level handler and map validation entries into `error.details`.
**Warning signs:** Mixed error body shapes across endpoints in tests.

### Pitfall 2: Status endpoint accidentally mutates message workflow
**What goes wrong:** Polling changes message state unexpectedly or advances processing.
**Why it happens:** Shared function side effects are called from `/message_status`.
**How to avoid:** Separate read-only status fetch from processing transitions.
**Warning signs:** Repeated polling produces different business outcomes without new input.

### Pitfall 3: Session state checks collapse into a single unauthorized status
**What goes wrong:** Missing/unauthorized/expired/nonexistent all return same code.
**Why it happens:** Session resolver lacks explicit branch mapping.
**How to avoid:** Encode ordered checks and map exactly to 404/401/410 per locked decision.
**Warning signs:** Client cannot distinguish retry vs re-auth vs terminal session loss.

## Code Examples

Verified patterns from official sources:

### Typed Response Contract
```python
# Source: https://fastapi.tiangolo.com/tutorial/response-model/
@app.get("/items/", response_model=list[Item])
async def read_items() -> Any:
    return [{"name": "Portal Gun", "price": 42.0}]
```

### Request Validation + Pydantic Model Parsing
```python
# Source: https://fastapi.tiangolo.com/tutorial/body/
class Item(BaseModel):
    name: str
    price: float
```

### UUIDv4 Generation
```python
# Source: https://docs.python.org/3/library/uuid.html
from uuid import uuid4
session_id = str(uuid4())
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ad-hoc dict payloads for API I/O | Typed request/response schemas with OpenAPI-backed contracts | Matured across FastAPI + Pydantic v2 ecosystem | Better client reliability and generated SDK compatibility. |
| Endpoint-local error shaping | Global exception normalization + machine-readable envelope | Widely adopted API reliability practice | Uniform client error handling across all failure modes. |
| Implicit status handling | Explicit state-machine responses | Current async API design norm | Deterministic polling behavior and easier client orchestration. |

**Deprecated/outdated:**
- Returning mixed error shapes (`detail` for some paths, custom object for others): replaced by a single envelope contract.

## Open Questions

1. **Session expiration policy details**
   - What we know: Expired sessions must return `410`.
   - What's unclear: Absolute TTL vs inactivity timeout and concrete duration.
   - Recommendation: Decide one policy in planning and encode in `SessionStore` with explicit tests.

2. **Next-message consumption semantics**
   - What we know: Client fetches next assistant response in async flow.
   - What's unclear: Whether retrieval is idempotent, cursor-based, or destructive pop.
   - Recommendation: Lock deterministic behavior in contract doc and tests before implementation.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | FastAPI runtime and tests | ✓ | 3.14.0 | — |
| fastapi | API routing/contracts | ✓ | 0.135.2 | Install via pip if missing |
| pydantic | Schema validation | ✓ | 2.12.5 | Install via pip if missing |
| pytest | Validation architecture tests | ✓ | 9.0.2 | Install via pip if missing |
| uvicorn | Local API serving | ✓ | 0.42.0 | `fastapi dev` style local runner if needed |

**Missing dependencies with no fallback:**
- None.

**Missing dependencies with fallback:**
- None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + FastAPI TestClient |
| Config file | none — defaults currently used |
| Quick run command | `pytest tests/test_auth.py -x` |
| Full suite command | `pytest -x` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | Start async chat returns valid session handle and passes auth gate | integration | `pytest tests/test_api_async_contracts.py::test_start_chat_returns_uuid_session_id -x` | ❌ Wave 0 |
| API-02 | Poll status returns structured lifecycle state | integration | `pytest tests/test_api_async_contracts.py::test_message_status_returns_structured_state -x` | ❌ Wave 0 |
| API-03 | Next-message follows expected async contract | integration | `pytest tests/test_api_async_contracts.py::test_next_message_contract_flow -x` | ❌ Wave 0 |
| API-04 | Invalid payloads return schema validation errors in unified envelope | integration | `pytest tests/test_api_async_contracts.py::test_invalid_payload_returns_enveloped_validation_error -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_api_async_contracts.py -x`
- **Per wave merge:** `pytest -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_api_async_contracts.py` — covers API-01..API-04 contract paths
- [ ] Shared error-envelope assertions helper in `tests/conftest.py` or `tests/helpers.py`
- [ ] Optional strict schema tests for status enum transitions (unit-level around state model)

## Sources

### Primary (HIGH confidence)
- [FastAPI - Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/) - custom exception handlers and validation override behavior
- [FastAPI - Response Model](https://fastapi.tiangolo.com/tutorial/response-model/) - response contract validation/filtering behavior
- [FastAPI - Request Body](https://fastapi.tiangolo.com/tutorial/body/) - Pydantic request model validation flow
- [Pydantic Models](https://docs.pydantic.dev/latest/concepts/models/) - model validation/serialization guarantees
- [Python uuid module](https://docs.python.org/3/library/uuid.html) - UUIDv4 generation and parsing behavior
- Local codebase: `src/api/chat.py`, `src/sessions/store.py`, `src/auth/errors.py`, `tests/test_auth.py`, `tests/conftest.py`

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified from local environment and official docs alignment.
- Architecture: HIGH - directly grounded in current code structure and FastAPI official patterns.
- Pitfalls: MEDIUM-HIGH - derived from current implementation gaps plus framework-documented behavior.

**Research date:** 2026-03-27
**Valid until:** 2026-04-26
