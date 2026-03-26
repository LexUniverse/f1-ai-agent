# Phase 1: Access Control - Research

**Researched:** 2026-03-26  
**Domain:** FastAPI access control with session-bound authorization  
**Confidence:** HIGH

## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | User can access assistant only with a valid personal access code from allowlist. | Recommends env-backed allowlist parser, session authorization state, and request guard dependency for all protected endpoints. |
| AUTH-02 | User with invalid code is denied access with explicit unauthorized message. | Defines stable error contract (`AUTH_INVALID_CODE`), RU-facing unauthorized text, and pre-processing auth gate to block downstream chat flow. |

## Summary

Phase 1 should implement a deterministic auth gate at session creation and enforce that gate before any downstream message processing. Because this project is at roadmap start and has no existing application code, the most reliable plan is to establish small, explicit auth modules that Phase 2 can reuse directly for async endpoint contracts.

Given locked decisions, this should not introduce database-backed identity yet. Use a comma-separated env allowlist, normalize incoming codes, persist only session-level authorization state, and add a minimal in-memory brute-force cooldown keyed by IP and/or session bootstrap identifier. Keep behavior explicit: unauthorized responses must include both machine code and RU user message.

Primary risk is accidental bypass (calling chat processing before auth guard) and observability leaks (logging full codes). Plan tasks should therefore include mandatory pre-handler guard checks, masked logging helper, and targeted auth tests that prove downstream handlers are never invoked for unauthorized calls.

**Primary recommendation:** Build a dedicated `auth` boundary now (allowlist parsing, validator, session guard, failure limiter) and make every protected endpoint consume it as a hard dependency.

## Project Constraints (from .cursor/rules/)

No project rule files were found in `.cursor/rules/`; no additional repository-specific coding constraints are enforced beyond phase/context decisions.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.135.2 | API endpoints and dependency-injected auth guards | Native request dependency model cleanly enforces pre-handler authorization checks. |
| Pydantic | 2.12.5 | Typed auth request/response/error models | Ensures stable machine-readable unauthorized payload contracts. |
| Uvicorn | 0.42.0 | ASGI runtime for local/prod serving | Standard runtime for FastAPI apps and straightforward operational setup. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `hmac` | built-in | Constant-time code comparison | Use for code equality check to reduce timing-leak risk in auth checks. |
| Python stdlib `time` / monotonic clock | built-in | Cooldown window tracking | Use for lightweight per-IP/per-session failure windows in v1. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Env allowlist only | Redis-backed allowlist + counters | Better distributed limits, but adds infra and is out of current phase scope. |
| In-memory cooldown | Reverse-proxy/WAF rate limits | Stronger edge protection, but requires deployment-specific infrastructure and does not replace app-level auth semantics. |

**Installation:**
```bash
pip install "fastapi==0.135.2" "pydantic==2.12.5" "uvicorn==0.42.0"
```

**Version verification:** Verified via `python3 -m pip index versions` on 2026-03-26:
- `fastapi`: latest `0.135.2`
- `pydantic`: latest `2.12.5`
- `uvicorn`: latest `0.42.0`

## Architecture Patterns

### Recommended Project Structure
```
src/
├── api/              # FastAPI endpoints and request models
├── auth/             # allowlist, validator, cooldown, session auth guard
└── sessions/         # session lifecycle + auth binding to session state
```

### Pattern 1: Session Bootstrap Gate
**What:** Validate access code only at `/start_chat`, then attach `authorized=true` to session state.  
**When to use:** Every new chat session creation flow.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/dependencies/
def start_chat(req: StartChatRequest, client_ip: str) -> StartChatResponse:
    auth_result = validate_access_code(req.access_code, client_ip)
    if not auth_result.ok:
        raise unauthorized_error("AUTH_INVALID_CODE")
    session_id = create_session(authorized=True)
    return StartChatResponse(session_id=session_id)
```

### Pattern 2: Pre-Handler Authorization Dependency
**What:** Protected endpoints (`/message_status`, `/next_message`) must require a guard that checks session authorization before handler logic.  
**When to use:** All downstream chat endpoints.
**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/dependencies/
def require_authorized_session(session_id: str) -> Session:
    session = load_session(session_id)
    if not session or not session.authorized:
        raise unauthorized_error("AUTH_UNAUTHORIZED")
    return session
```

### Anti-Patterns to Avoid
- **Prompt-layer auth only:** Never rely on LLM prompt instructions to block unauthorized users.
- **Repeated code prompts per message:** Violates locked decision D-02 and harms UX.
- **Logging raw codes:** Must mask values in logs; raw values are sensitive operational data.
- **Auth check after chat pipeline call:** Unauthorized requests must be rejected before downstream processing starts.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP auth enforcement | Manual inline checks in every route body | FastAPI dependency guard | Centralized, testable, and difficult to bypass accidentally. |
| Error payload consistency | Ad hoc dict responses | Pydantic error schema | Guarantees stable machine-readable code contract. |
| Timing-safe compare | Plain `==` for secrets | `hmac.compare_digest` | Reduces side-channel leakage for string comparisons. |

**Key insight:** Hand-rolled, scattered auth logic creates bypass risk; centralized dependency guards plus typed errors enforce correctness with fewer moving parts.

## Common Pitfalls

### Pitfall 1: Endpoint bypass due to missing dependency
**What goes wrong:** One protected endpoint forgets auth guard and reaches chat processing unauthenticated.  
**Why it happens:** Guard checks are done manually inside handlers instead of dependency injection.  
**How to avoid:** Require `require_authorized_session` dependency in every chat endpoint signature.  
**Warning signs:** Unauthorized calls produce non-auth errors or invoke business logic traces.

### Pitfall 2: Cooldown keyed only by session ID
**What goes wrong:** Attackers bypass brute-force limiter by creating new sessions repeatedly.  
**Why it happens:** Limiter ignores client-level keying (IP/device token).  
**How to avoid:** Track failures on both IP and session bootstrap context; enforce temporary lockouts.  
**Warning signs:** High failed-code volume across many short-lived sessions from same IP range.

### Pitfall 3: Code normalization mismatch
**What goes wrong:** Valid codes fail due to inconsistent whitespace handling or storage parsing bugs.  
**Why it happens:** Normalization performed on input but not allowlist, or vice versa.  
**How to avoid:** Normalize both sides with one shared utility and test representative inputs.  
**Warning signs:** Intermittent auth failures for copied/pasted codes.

## Code Examples

Verified patterns from official sources:

### FastAPI dependency guard
```python
# Source: https://fastapi.tiangolo.com/tutorial/dependencies/
from fastapi import Depends, HTTPException

def require_authorized_session(session_id: str):
    session = session_store.get(session_id)
    if not session or not session.authorized:
        raise HTTPException(status_code=401, detail={"code": "AUTH_UNAUTHORIZED"})
    return session
```

### Typed error payload via model
```python
# Source: https://docs.pydantic.dev/latest/concepts/models/
from pydantic import BaseModel

class AuthError(BaseModel):
    code: str
    message: str
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Route-local auth checks | Dependency-injected centralized guard | FastAPI best-practice era | Fewer bypass bugs and simpler testing. |
| Unstructured auth errors | Typed machine-readable auth envelopes | Pydantic v2 ecosystem maturity | Cleaner client handling and requirement traceability. |

**Deprecated/outdated:**
- Prompt-only authorization behavior: not acceptable for backend access control; must be deterministic server logic.

## Open Questions

1. **Cooldown default values (threshold/window)**
   - What we know: Decision allows Claude discretion for defaults.
   - What's unclear: Product tolerance for false lockouts vs brute-force resistance.
   - Recommendation: Start with conservative defaults (e.g., 5 failures / 5 minutes / 10-minute cooldown) and tune from logs.

2. **HTTP status mapping for invalid vs missing vs expired-session**
   - What we know: Need explicit machine code and user-facing RU message.
   - What's unclear: Whether all auth denials should collapse to one status for simplicity.
   - Recommendation: Use `401` for invalid/missing credentials and session unauthenticated; reserve `429` for cooldown lockouts.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | FastAPI auth service implementation | ✓ | 3.14.0 | — |
| pip3 | Installing backend dependencies | ✓ | 25.2 | — |
| node/npm | GSD workflow tooling only | ✓ | node 24.11.1 / npm 11.6.2 | — |
| docker | Optional containerized verification later | ✓ | 28.5.2 | Run locally without Docker |

**Missing dependencies with no fallback:**
- None.

**Missing dependencies with fallback:**
- None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (to be initialized in this phase) |
| Config file | none — see Wave 0 |
| Quick run command | `pytest tests/test_auth.py -x -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | Valid allowlist code creates authorized session | unit/integration | `pytest tests/test_auth.py::test_start_chat_valid_code_authorizes -x -q` | ❌ Wave 0 |
| AUTH-02 | Invalid/missing code denied with explicit unauthorized message | unit/integration | `pytest tests/test_auth.py::test_start_chat_invalid_code_rejected -x -q` | ❌ Wave 0 |
| AUTH-02 | Unauthorized blocked before downstream processing | integration | `pytest tests/test_auth.py::test_unauthorized_blocked_before_chat_pipeline -x -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_auth.py -x -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_auth.py` — covers AUTH-01 and AUTH-02 auth flows
- [ ] `tests/conftest.py` — session store and request fixture setup
- [ ] Framework install: `pip install pytest` — if not already present

## Sources

### Primary (HIGH confidence)
- [FastAPI Dependencies docs](https://fastapi.tiangolo.com/tutorial/dependencies/) - dependency-based request guards and pre-handler validation pattern.
- [FastAPI Security docs](https://fastapi.tiangolo.com/tutorial/security/) - authentication/authorization integration patterns.
- [Pydantic Models docs](https://docs.pydantic.dev/latest/concepts/models/) - typed schema definitions for stable API contracts.
- Local project context files (`.planning/phases/01-access-control/01-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/config.json`) - locked decisions and requirement traceability.

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` - project-aligned baseline stack and implementation hazards.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - versions validated directly from PyPI index and aligned with project stack docs.
- Architecture: HIGH - directly constrained by locked decisions and FastAPI official dependency model.
- Pitfalls: MEDIUM-HIGH - supported by project pitfall research and common backend auth failure modes.

**Research date:** 2026-03-26  
**Valid until:** 2026-04-25
