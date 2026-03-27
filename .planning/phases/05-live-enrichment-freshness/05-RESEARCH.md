# Phase 5: Live Enrichment & Freshness - Research

**Researched:** 2026-03-27  
**Domain:** Conditional live HTTP enrichment (f1api.dev) behind FastAPI `/next_message`, Pydantic contracts, Russian UX  
**Confidence:** MEDIUM-HIGH (official f1api.dev + httpx docs verified; no published rate-limit contract found)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Content below is copied from `.planning/phases/05-live-enrichment-freshness/05-CONTEXT.md` (`<decisions>` / Implementation Decisions).

**Live-call trigger & routing (LIVE-01)**

- **D-01:** **Always run historical retrieval first** (current `resolve_entities` → `retrieve_historical_context` → `format_evidence` order). No live calls before that completes.
- **D-02:** Consider a **live enrichment attempt** only when **both** hold: (a) the question **requires current/live data** per a **deterministic gate**, and (b) **either** `evidence` is **empty** after formatting **or** the gate marks the query as **live-primary** (e.g. standings, schedule, “who leads now”). For v1, prioritize the **empty-evidence** branch so behavior stays easy to test; **optional second branch** (live-primary with weak RAG) is **Claude’s discretion** if tests stay stable.
- **D-03:** **Live gate (intent):** Use a **normalized_query** (and/or original user text) check with an **explicit allowlist** of patterns/keywords (RU/EN) for “current”, “now”, “latest standings”, “next race”, “calendar”, etc. **Planner** maintains the list as code + tests; avoid LLM-based routing in this phase.
- **D-04:** If historical path already yields **non-empty evidence** and the question is **not** live-primary per D-03, **do not** call the live API—return the existing Phase 4 success payload.

**`details` / API contract (LIVE-01, LIVE-03)**

- **D-05:** When live data contributes to a **successful** answer, include a **`details["live"]`** object (Pydantic-serialized to dict) alongside existing keys. **Minimum fields:** `as_of` (string, UTC ISO-8601 with `Z`), `provider` (literal `"f1api.dev"`). **Optional:** `resource` or `endpoint_key` for traceability/debug (Claude’s discretion).
- **D-06:** Keep **historical provenance** in `details["evidence"]` (f1db-backed). **Do not** mix live rows into `evidence` as fake `EvidenceItem`s unless the planner adds a **clear, tested** mapping; **default for v1:** `evidence` remains historical-only; live facts live under **`live`** (and/or a dedicated `live_facts` shape) so provenance stays auditable.
- **D-07:** **`message` (RU)** must remain a **short user-facing line**. When live is used, it **must visibly reflect freshness** (e.g. include an **`Актуально на …`** or equivalent substring tying to the same instant as `details.live.as_of`—exact wording Claude’s discretion).
- **D-08:** Success `details["code"]` remains **`"OK"`** for both purely historical and live-enriched successes; consumers use **`"live" in details`** to detect live usage (avoid proliferating success codes unless tests demand a distinct `OK_LIVE`).

**Degraded mode & outages (LIVE-02)**

- **D-09:** On **timeout, transport error, HTTP 5xx, or open circuit** when a **live call was required** (gate passed), return **`status: "failed"`** with **`details["code"] == "LIVE_UNAVAILABLE"`**. **Do not** use `RETRIEVAL_NO_EVIDENCE` for API outages.
- **D-10:** **`details`** on that branch: include **`code`**, **`evidence": []`**, and **omit** `structured_answer` / `confidence` (same hygiene as abstention path). Optional: `details["live"]` with `{"error": "..."}` for debug—Claude’s discretion if tests lock it.
- **D-11:** **`message`** must be a **fixed Russian string** (single canonical template) that states that **live data is temporarily unavailable** and that the assistant **cannot answer the current-data part**—**no fabricated results**. Exact sentence Claude’s discretion; must be **pytest-stable**.

**Client resilience & `as_of` semantics (LIVE-03)**

- **D-12:** Implement **`f1api.dev`** behind a **dedicated client module** (e.g. `src/integrations/` or `src/live/`) with **configurable timeout** (default **≤ 10s**), **bounded retries** on safe GETs (count/backoff: Claude’s discretion), and a **circuit breaker** after repeated failures.
- **D-13:** **`as_of`**: Prefer a **timestamp from the API payload** when the client can extract it; otherwise use **UTC ISO-8601** time of the **successful response completion** at the server. Always normalize to **UTC** with **`Z`** in JSON.
- **D-14:** **Caching (optional v1):** Short TTL cache for identical live requests is **Claude’s discretion**; if added, **`as_of` must still reflect** the **data freshness rule** (either API timestamp or cache + stale metadata—planner documents choice in PLAN).

### Claude's Discretion

- Exact **keyword/pattern list** for D-03 and any **low-score + live** heuristic.
- **Pydantic** names for nested `live` shapes beyond the minimum in D-05.
- **Circuit breaker** thresholds, **retry** counts, **cache TTL**.
- **Exact Russian strings** for D-07 and D-11 (must stay **test-locked** once chosen).

### Deferred Ideas (OUT OF SCOPE)

- **LangGraph / multi-agent** routing (named in PROJECT.md) — not part of Phase 5 delivery.
- **Merging historical + live** in one synthesized narrative with conflict resolution — only if explicitly planned; v1 may ship **live-only fallback when RAG is empty** first.
- **Docker / production deploy** — v2 / out of scope per REQUIREMENTS.

### Reviewed Todos (not folded)

- None (todo match-phase returned no items).

**None otherwise — discussion stayed within Phase 5 scope.**

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LIVE-01 | User receives live-enriched answer when RAG context is insufficient and live data is required. | Deterministic live gate (D-03); call f1api only after retrieval (D-01) when gate + empty evidence (D-02); extend `next_message` success path with optional live fetch + answer synthesis using live JSON (dedicated `details["live"]` D-05–D-06). |
| LIVE-02 | User receives clear degraded-mode message when live API is unavailable. | Map timeouts, transport errors, HTTP 5xx, open breaker to `failed` + `LIVE_UNAVAILABLE` (D-09–D-11); resilient client (D-12). |
| LIVE-03 | User answer includes freshness metadata (`as_of`) for live-dependent responses. | ISO-8601 UTC `Z` in `details.live.as_of` (D-05, D-13); surface same instant in RU `message` (D-07). |

</phase_requirements>

## Project Constraints (from .cursor/rules/)

No `.cursor/rules/` files were present in the workspace at research time — no additional project rule directives beyond GSD phase CONTEXT and existing code style.

## Summary

Phase 5 adds a **thin, testable live layer** after the existing historical RAG path in `src/api/chat.py`. The public **f1api.dev** API exposes JSON under **`https://f1api.dev/api/...`** with **GET** semantics; sampled documentation does **not** describe API keys (site positions the API as free/open). Planners should treat **standings** and **schedule** as first-class endpoints (`current/next`, `current/drivers-championship`, etc.) and design the client around **explicit resource keys** so `details.live` can carry `provider`, `as_of`, and optional `endpoint_key` (D-05).

Use **`httpx`** (already in project research stack at **0.28.1**, verified installed in this environment) with **`httpx.Timeout`** for the ≤10s budget (D-12). Built-in **`HTTPTransport(retries=n)`** only retries **connection** failures (`ConnectError`, `ConnectTimeout`); for **HTTP 503** or read timeouts, add **`tenacity`**-style bounded retries in application code or a small wrapper — official httpx docs explicitly steer complex retry behavior to tools like [tenacity](https://github.com/jd/tenacity). A **circuit breaker** is not provided by httpx; use **`pybreaker`** (latest **1.4.1** on PyPI) or a **minimal in-module** open/half-open/closed state machine colocated with the client (`src/integrations/f1api_client.py` or `src/live/client.py`).

**Primary recommendation:** Implement `F1ApiClient` in **`src/integrations/`** (matches `ARCHITECTURE.md`), wire it from **`next_message`** via a small orchestration function; keep **sync** `httpx.Client` to match the current synchronous route; gate live calls with **pure string/pattern tests**; return **`LIVE_UNAVAILABLE`** without fabricating standings/schedule JSON.

## Executive summary (planner-facing)

1. **Order of operations:** unchanged through `format_evidence`; then **if** live gate passes **and** (empty evidence **or** optional live-primary branch), call f1api; else preserve Phase 4 branches (`RETRIEVAL_NO_EVIDENCE` only when live not applicable).  
2. **Contracts:** extend response `details` with `live: { as_of, provider, ... }` on success; on live-required failure use `code: LIVE_UNAVAILABLE` and abstention-shaped `details` (D-10).  
3. **HTTP:** one module owns base URL, timeouts, retries, breaker, and status-code mapping; **env vars** e.g. `F1API_BASE_URL` (default `https://f1api.dev`), `F1API_TIMEOUT_SECONDS` (default `10`), optional `F1API_BREAKER_FAIL_MAX`, `F1API_RETRY_ATTEMPTS`.  
4. **Tests:** no network in CI — mock **`httpx`** transport or patch client factory; lock RU strings and JSON shapes.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `httpx` | **0.28.1** (PyPI current; verified installed) | Sync HTTP client to f1api.dev | Matches `.planning/research/STACK.md`; first-class timeouts; `MockTransport` for tests |
| `fastapi` | **0.135.2** (installed) | Existing `/next_message` surface | No change to framework choice |
| `pydantic` | v2 (via FastAPI) | `LiveDetails`, optional nested models | Aligns with `api_contracts.py` patterns |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|-----------|-------------|
| `tenacity` | planner-pinned | Retry on 503 / read timeout with backoff | When built-in transport retries are insufficient (httpx official guidance) |
| `pybreaker` | **1.4.1** (PyPI) | Circuit breaker decorator / context | Satisfies D-12 without hand-rolling distributed breaker semantics |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pybreaker` | ~40 LOC manual breaker in `src/live/circuit.py` | Fewer deps; planner must test state transitions |
| `tenacity` | Manual retry loop | More boilerplate; easier to get wrong on idempotency |
| Sync `httpx` | `httpx.AsyncClient` + async route | Aligns with async FastAPI eventually; **larger** change than Phase 5 scope |

**Installation note:** Repository has **no `pyproject.toml`** in tree; dependencies are environment-managed. For new deps: add to the project’s canonical manifest when introduced, or document in PLAN Wave 0.

**Version verification (2026-03-27):**

```bash
python3 -m pip index versions httpx | head -1   # 0.28.1
python3 -m pip index versions pybreaker | head -1  # 1.4.1
```

## f1api.dev integration notes

**Base URL (public docs):** `https://f1api.dev` — documentation states data is fetched as JSON from this host ([F1 API docs](https://f1api.dev/docs), [home](https://f1api.dev/)).

**Auth:** Sampled endpoint pages and “Try it” URLs use bare HTTPS GET with **no** API key parameter. **Confidence MEDIUM:** treat as **unauthenticated public GET** unless a future doc adds keys; do not hard-code secrets.

**CORS / methods:** Live probe returned **HTTP 200** with `access-control-allow-origin: *` and `access-control-allow-methods: GET` for `/api/current/next`.

**Endpoints most relevant to “current season / schedule / standings”** (from [standings](https://f1api.dev/docs/standings), [races](https://f1api.dev/docs/races)):

| Use case | Documented path pattern | Example “Try it” URL |
|----------|-------------------------|----------------------|
| Next race (calendar) | `GET api/current/next` | `https://f1api.dev/api/current/next` |
| Last race | `GET api/current/last` | (see races docs) |
| Current season race list | `GET api/current` | (see races docs) |
| Driver standings (current) | `GET api/current/drivers-championship` | `https://f1api.dev/api/current/drivers-championship` |
| Constructor standings (current) | `GET api/current/constructors-championship` | (see standings docs) |
| Season list / historical year | `/api/{year}/...`, seasons index | Per docs trees |

**Response shape notes for `as_of` (D-13):** Example JSON for `current/next` includes **`schedule.race.date`** strings but **no single server timestamp field**. Plan for **`as_of` = response completion time (UTC Z)** unless a stable timestamp field is identified across endpoints; optionally derive a **logical** time from race schedule for messaging (document in PLAN — do not claim API provides `as_of` until verified per endpoint).

**Status codes (documented on sample pages):** 200 success, 404 not found, 500 internal error — map **5xx and transport errors** to `LIVE_UNAVAILABLE` when live was required (D-09). **404** may mean “no next race” vs true outage — planner should decide **per endpoint** whether 404 is **degraded** or **valid empty** (critical product decision).

**Rate limits:** Not stated on fetched pages — **open risk**; optional TTL cache (D-14) mitigates.

## FastAPI / httpx patterns: timeout, retries, circuit breaker

### Timeout

Use granular timeout on the client (covers connect + read within budget):

```python
import httpx

timeout = httpx.Timeout(10.0)  # default ≤10s per D-12; override via env
client = httpx.Client(base_url="https://f1api.dev", timeout=timeout)
```

Source: [httpx timeouts](https://www.python-httpx.org/advanced/timeouts/) (standard pattern).

### Retries

```python
transport = httpx.HTTPTransport(retries=1)  # ConnectError / ConnectTimeout only
client = httpx.Client(transport=transport, base_url="https://f1api.dev", timeout=timeout)
```

For **503 / read timeouts**, httpx recommends **tenacity** (or equivalent) — see [Transports - HTTPX](https://www.python-httpx.org/advanced/transports/).

### Circuit breaker (Python)

- **`pybreaker`:** decorate or wrap `client.get(...)`; on `CircuitBreakerError`, map to **open circuit** branch of D-09 without calling the network.
- **Manual:** keep failure counts + opened-until timestamp in a **module-level or app.state** object (sufficient for single-process MVP; document non-shared state if multiple workers).

### FastAPI wiring

- Instantiate **one shared client** at startup (`app.state.f1_client`) or use a **factory** in a dependency for test injection.
- Keep **route handler** thin: `live_result = enrich_if_needed(...)` where enrichment calls the integration module only.

### Testing

- **`httpx.MockTransport`** (official) or **`pytest-httpx`** / **RESpx** for declarative mocks.

## Mapping CONTEXT decisions D-01..D-14 → implementation anchors

| ID | Implementation hook |
|----|---------------------|
| D-01 | `next_message`: no `F1ApiClient` call before `format_evidence` completes (`chat.py` ordering). |
| D-02 | After `if not evidence:` branch, **sub-gate** “live needed?” before returning `RETRIEVAL_NO_EVIDENCE`; if live not needed, keep current abstention. If live needed and call succeeds, build success payload with `live`. |
| D-03 | New module e.g. `src/live/gate.py` or `src/integrations/live_gate.py`: pure function `(normalized_query, session_text) -> LiveIntent`. |
| D-04 | Early return when `evidence` non-empty and not live-primary — **no** HTTP call. |
| D-05–D-06 | `src/models/api_contracts.py`: `LiveDetails` model; `details["live"] = live.model_dump()`; `evidence` stays `EvidenceItem` list only. |
| D-07 | Build `message` in one place after live success; pytest asserts substring / regex for freshness. |
| D-08 | Keep `"code": "OK"`; tests use `"live" in details`. |
| D-09–D-11 | Unified `except` / status check path → `store.set_status(..., "failed", "LIVE_UNAVAILABLE")` and fixed RU `message`. |
| D-12 | `src/integrations/f1api_client.py`: timeout, retries, breaker around `httpx`. |
| D-13 | Helper `live_as_of_utc_z(response, t_completed: datetime) -> str`. |
| D-14 | Optional cache dict or `cachetools.TTL` — document `as_of` semantics in PLAN if used. |

## Architecture Patterns

### Recommended layout (concrete)

```
src/
├── api/chat.py              # orchestration only
├── integrations/
│   └── f1api_client.py      # HTTP + breaker + retry
├── live/                    # optional package
│   ├── gate.py              # deterministic live intent
│   └── enrich.py            # compose RAG outcome + live JSON → details/message
└── models/api_contracts.py    # LiveDetails, optional LiveErrorDetails
```

### Pattern: adapter boundary

**What:** All f1api URLs, query params, and JSON parsing live in **one** client class.  
**When:** Always — satisfies ARCHITECTURE.md integration boundary and D-12.

### Anti-patterns

- **LLM-based routing** for live vs not (explicitly excluded D-03).
- **Stuffing live rows into `EvidenceItem`** without a designed mapping (default forbidden D-06).
- **Using `RETRIEVAL_NO_EVIDENCE` for HTTP outages** when live was required (forbidden D-09).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP connection retries | Custom socket loop | `httpx.HTTPTransport(retries=n)` + optional tenacity | Battle-tested; maps to official docs |
| URL encoding / session cookies | Ad-hoc strings | `httpx` `params=`, `Client` | Prevents subtle URL bugs |
| Parser for every endpoint by hand | Giant `if/else` in route | Typed `TypedDict` / Pydantic models per **selected** endpoints | Limits scope; eases tests |

**Key insight:** Breaker + timeout + stable error mapping are **product requirements** (LIVE-02); a thin wrapper around httpx is less risky than a fully custom HTTP stack.

## Common Pitfalls

### Pitfall 1: Calling live API before retrieval finishes

**What goes wrong:** Violates RAG-first policy and D-01.  
**How to avoid:** Structure code so the live branch is **nested** under post-retrieval logic only.

### Pitfall 2: `as_of` drift vs user-visible “Актуально на …”

**What goes wrong:** Users see a time that does not match `details.live.as_of`.  
**How to avoid:** Single `as_of` variable passed into both `details` and `message` formatting (D-07, D-13).

### Pitfall 3: Treating 404 as outage

**What goes wrong:** Unnecessary `LIVE_UNAVAILABLE` when “no next race” is valid.  
**How to avoid:** Per-endpoint policy table in PLAN; tests for 404 behavior.

### Pitfall 4: Circuit opens globally on one bad deploy

**What goes wrong:** All users blocked until reset.  
**How to avoid:** Conservative thresholds, optional half-open probe, log breaker transitions.

### Pitfall 5: Flaky CI due to real network

**What goes wrong:** Tests hit f1api.dev and fail intermittently.  
**How to avoid:** Always mock HTTP; optional **manual** smoke script outside pytest.

## Code Examples

### httpx client with timeout and transport retries

```python
import httpx

transport = httpx.HTTPTransport(retries=1)
timeout = httpx.Timeout(10.0)
with httpx.Client(
    base_url="https://f1api.dev",
    transport=transport,
    timeout=timeout,
    headers={"User-Agent": "f1-assistant/1.0"},
) as client:
    r = client.get("/api/current/next")
    r.raise_for_status()
    data = r.json()
```

Source: [HTTPX Transports](https://www.python-httpx.org/advanced/transports/)

### MockTransport for unit tests

```python
import httpx

def handler(request):
    return httpx.Response(200, json={"race": [], "season": 2026})

client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://f1api.dev")
```

Source: [HTTPX Transports — Mock transports](https://www.python-httpx.org/advanced/transports/)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `requests` in sync apps | `httpx` with timeout + mock transports | httpx 0.28 era | Better test hooks, HTTP/2 optional |
| Retry everything blindly | Connect-only transport retries + policy for idempotent GET | httpx docs | Avoids unsafe retry of non-idempotent ops |

**Deprecated/outdated:** Relying on LLM to “decide” tool use for outage-sensitive paths — replaced by deterministic gates per Phase 5 CONTEXT.

## Open Questions

1. **404 semantics for `current/next` when no race is scheduled**  
   - What we know: Docs list 404 as possible.  
   - What’s unclear: Product wants abstention vs empty live payload.  
   - Recommendation: Decide in PLAN with one pytest per behavior.

2. **Published rate limits**  
   - What we know: Not on sampled doc pages.  
   - Recommendation: Conservative client-side concurrency (1); optional cache D-14.

3. **Whether any endpoint returns a server `updated_at` suitable for `as_of`**  
   - What we know: `current/next` example lacks it.  
   - Recommendation: Audit chosen endpoints during implementation; default D-13 fallback.

## Environment Availability

Step 2.6 executed for external HTTP dependency.

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Outbound HTTPS to f1api.dev | LIVE-01..03 | ✓ (probe 200) | — | Mock in dev/test |
| `python3` | Runtime | ✓ | 3.14.0 (local) | CI matrix in PLAN |
| `httpx` | Client | ✓ | 0.28.1 | `pip install httpx` |
| `pybreaker` / `tenacity` | Breaker / retries | ✗ not installed | — | Add when implementing |

**Missing dependencies with no fallback:**

- None for research — implementation will add libraries if selected.

**Missing dependencies with fallback:**

- `pybreaker` — can implement minimal manual breaker instead.

## Risks and test strategy

| Risk | Mitigation | Test idea |
|------|------------|-----------|
| API schema drift | Pin client to documented fields; tolerate extra keys | Contract test on **mocked** JSON fixtures copied from docs |
| Latency spikes | Timeout 10s + breaker | Inject slow `MockTransport` → `LIVE_UNAVAILABLE` |
| False positive live gate | Strict allowlist + negatives | Parametrized tests: historical questions must not call client |
| RU copy regressions | Single constant `LIVE_UNAVAILABLE_MESSAGE_RU` | `assert response.json()["message"] == ...` |
| Double live calls | Optional TTL cache D-14 | Spy/mock call count = 1 for identical prompt |

**Layering:** unit tests for `gate` + `f1api_client`; integration tests for `/next_message` with **mocked** client on `app.state`.

## Validation Architecture

> Nyquist enabled (`workflow.nyquist_validation: true` in `.planning/config.json`).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `pytest.ini` (minimal `addopts`) |
| Quick run command | `cd /Users/alexshrestha/Documents/pet/AIAgent && python3 -m pytest tests/test_live_enrichment.py -x` (once added) |
| Full suite command | `cd /Users/alexshrestha/Documents/pet/AIAgent && python3 -m pytest` |

*If using uv with a future manifest:* `uv run pytest` from project root.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| LIVE-01 | Empty RAG + live gate → success with `details["live"]` and `code==OK` | integration | `python3 -m pytest tests/test_live_enrichment.py::test_live_enriches_when_rag_empty -x` | ❌ Wave 0 |
| LIVE-01 | Non-empty RAG + non-live query → no HTTP call | unit/integration | `python3 -m pytest tests/test_live_enrichment.py::test_no_live_call_when_evidence_present -x` | ❌ Wave 0 |
| LIVE-02 | Simulated 503/timeout → `failed`, `LIVE_UNAVAILABLE`, fixed RU message | integration | `python3 -m pytest tests/test_live_enrichment.py::test_live_unavailable_degraded -x` | ❌ Wave 0 |
| LIVE-03 | `details["live"]["as_of"]` ends with `Z` and matches message freshness rule | unit | `python3 -m pytest tests/test_live_as_of.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python3 -m pytest tests/test_live_enrichment.py -x`
- **Per wave merge:** full `python3 -m pytest`
- **Phase gate:** full suite green before `/gsd-verify-work`

### Mocking strategy (Nyquist Dimension 8)

1. **App-state injection:** `app.state.f1_client` or `app.state.f1_api` factory replaced in tests with mock implementing the same interface as `F1ApiClient`.  
2. **httpx.MockTransport:** ideal for **unit** tests of the client module in isolation.  
3. **`unittest.mock.patch`:** patch `integrations.f1api_client.fetch_*` used by `enrich.next_message` path.  
4. **No real network in default pytest** — optional `@pytest.mark.integration` + env `F1API_LIVE_TEST=1` for manual smoke.

### Wave 0 Gaps

- [ ] `tests/test_live_enrichment.py` — LIVE-01, LIVE-02 end-to-end via `TestClient`
- [ ] `tests/test_live_gate.py` — pure gate logic (D-03)
- [ ] `tests/test_f1api_client.py` — timeout, retries, breaker mapping (D-12)
- [ ] Document new deps in project manifest when repo gains `pyproject.toml` / `requirements.txt`

## Sources

### Primary (HIGH confidence)

- [F1 API documentation](https://f1api.dev/docs) — endpoint inventory, JSON examples  
- [Standings: current drivers championship](https://f1api.dev/docs/standings/current-drivers-championship) — example response fields  
- [Races: current next](https://f1api.dev/docs/races/current-next) — schedule JSON shape  
- [HTTPX Transports](https://www.python-httpx.org/advanced/transports/) — retries scope, MockTransport, tenacity pointer  

### Secondary (MEDIUM confidence)

- [f1api.dev home](https://f1api.dev/) — “free API” positioning; no rate-limit text  
- `.planning/research/STACK.md` — httpx 0.28.1 alignment  
- `.planning/research/PITFALLS.md` — live API resilience pitfall  

### Tertiary (LOW confidence)

- Web search summary on `httpx-retries` ecosystem — validate before adopting third-party transport wrappers  

## Metadata

**Confidence breakdown:**

- Standard stack: **HIGH** — httpx verified installed + official docs  
- Architecture: **HIGH** — aligns with CONTEXT + existing `chat.py`  
- f1api semantics (404, rate limits, auth): **MEDIUM** — gaps documented  
- Pitfalls: **MEDIUM-HIGH** — cross-checked with PITFALLS.md  

**Research date:** 2026-03-27  
**Valid until:** ~2026-04-27 (re-verify f1api docs if implementing later)
