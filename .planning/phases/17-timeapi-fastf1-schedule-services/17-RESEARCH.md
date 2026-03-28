# Phase 17: TimeAPI & FastF1 schedule services - Research

**Researched:** 2026-03-28  
**Domain:** HTTP time authority (TimeAPI.io) + FastF1 `EventSchedule` / pandas  
**Confidence:** HIGH (TimeAPI + FastF1 verified against live probe and official docs)

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TIME-01 | TimeAPI.io for current UTC/unix; timeout; one attempt or planned retry; on failure fixed RU degraded message or explicit fallback only if planned | httpx client pattern; response shapes verified; env timeout mirroring `TAVILY_TIMEOUT`; structured error + RU constant alongside `messages_ru.py` patterns |
| SCHED-01 | `fastf1.get_event_schedule(year)`; RoundNumber > 0; non-testing; next GP where next session UTC > TIME-01 now; default year from UTC now + year+1 rollover; payload: name, country/circuit fields from FastF1, Session* DateUtc subset + EventDate; ergast/pre-2018 caveats in verification | Official FastF1 event docs; `include_testing=False`; selection algorithm; `get_event_schedule` signature from docs.fastf1.dev |
</phase_requirements>

## Summary

Phase 17 adds **service-layer** modules under `src/integrations/` (no LangGraph tools here — Phase 18). The **single clock** for “сейчас” should come from **TimeAPI.io** using **httpx** with a **configurable timeout** and **one HTTP attempt** by default (retries only if explicitly added in PLAN.md). On failure, return a **structured error** plus a **fixed Russian degraded string**; do **not** silently substitute local system time unless the plan explicitly chooses that fallback (REQUIREMENTS default disfavors silent local clock).

**FastF1** supplies the calendar via `fastf1.get_event_schedule(year, include_testing=False, backend=None)`. For **2018+**, FastF1’s own backend exposes full **`Session1DateUtc`…`Session5DateUtc`** (naive UTC per docs). For **pre-2018** (or if `backend='ergast'`), session times are **partially assumed** from a conventional weekend layout — planners must treat historical schedule outputs as **approximate** for non-race sessions and document this wherever schedule results are described (README / docstrings in Phase 19+; module docstrings in Phase 17 as feasible).

**Year selection:** default **calendar year of UTC “now”** from TIME-01; if **no** grand prix remains in that season with a session strictly after `now`, load **`year + 1`** (covers late December when the next race is in January).

**Primary recommendation:** Implement `timeapi_client` (httpx, one shot, env timeout) and `f1_schedule_service` (pandas row logic + `get_event_schedule`) returning **Pydantic v2** models or typed dicts; test with **mocked httpx** and **monkeypatched or synthetic DataFrame** schedule data; optional **opt-in live** TimeAPI smoke behind an env flag.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 (pinned in repo) | Async-capable HTTP client; sync API available | Already in `requirements.txt`; requirement for this phase |
| fastf1 | **3.8.1** (verify: `pip index versions fastf1`, 2026-03-28) | `get_event_schedule`, `EventSchedule` DataFrame | Official F1 schedule integration used in REQUIREMENTS |
| pydantic | v2 (repo constraint) | Structured service results / errors | Matches existing API stack |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pandas | (fastf1 dependency) | Schedule is a `DataFrame` / row `Series` | Always when touching `EventSchedule` |
| pytest | ≥8 (repo) | Unit tests | All automated verification |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| httpx | `requests` (as in `tavily_tool.py`) | User/phase mandate is httpx for TimeAPI; keep Tavily on requests unless refactoring |
| Manual Ergast HTTP | FastF1 | Reinvents caching, backends, column layout — avoid |

**Installation (Phase 17 task):**

```bash
# Add to requirements.txt, then:
pip install 'fastf1>=3.8.0,<4'
```

**Version verification (executed 2026-03-28):** `pip index versions fastf1` → latest **3.8.1**. Repo **httpx** pinned **0.28.1**.

## Architecture Patterns

### Recommended project structure

```
src/integrations/
├── __init__.py          # export public service entrypoints only
├── timeapi_client.py    # fetch UTC + unix; env timeout; structured errors
├── f1_schedule_service.py  # next GP resolution vs TimeAPI instant
└── messages_ru.py       # TIMEAPI_UNAVAILABLE_MESSAGE_RU (fixed degraded text)
```

Mirror **`src/graph/tavily_tool.py`** patterns:

- Read **timeout from environment** with a numeric default (e.g. `TIMEAPI_TIMEOUT` default `10`, same spirit as `TAVILY_TIMEOUT` in ```66:66:src/graph/tavily_tool.py
    timeout = float(os.environ.get("TAVILY_TIMEOUT", "10"))
```).
- Define **small exception types** (e.g. `TimeApiError`, `ScheduleResolutionError`) analogous to `TavilyConfigError`.
- **No silent failure:** return or raise in a way Phase 18 tools can surface as **explicit tool errors**.

### Pattern: TimeAPI single GET with bounded timeout

**What:** One `httpx.Client` request to `GET https://timeapi.io/api/v1/time/current/utc` and/or `.../unix` with `timeout=` from env.  
**When to use:** Every TIME-01 call.  
**Live response shapes verified 2026-03-28:**

- `GET /api/v1/time/current/unix` → JSON `{"unix_timestamp": <int>}`  
- `GET /api/v1/time/current/utc` → JSON `{"utc_time":"<ISO-8601>Z"}` (Swagger’s full `CurrentTime` schema may apply to other endpoints; treat **parsed JSON** defensively).

**Example:**

```python
# Source: https://www.timeapi.io/swagger/v1/swagger.json + live probe
import os
import httpx

BASE = "https://timeapi.io"
timeout = float(os.environ.get("TIMEAPI_TIMEOUT", "10"))

with httpx.Client(timeout=timeout) as client:
    r = client.get(f"{BASE}/api/v1/time/current/unix")
    r.raise_for_status()
    data = r.json()
    unix_ts = int(data["unix_timestamp"])
```

Use **`raise_for_status()`** and catch **`httpx.HTTPError`**, **`httpx.TimeoutException`**, **`httpx.RequestError`** to build structured errors.

### Pattern: Next grand prix vs authoritative `now`

**What:**

1. Obtain **`now_utc`** from TimeAPI (normalize to **`pd.Timestamp`** or **`datetime`** consistent with naive UTC from FastF1).
2. **`year = now_utc.year`** (from UTC instant).
3. `schedule = fastf1.get_event_schedule(year, include_testing=False)` — default API is `include_testing=True`, so **pass `False`** ([docs](https://docs.fastf1.dev/fastf1.html#get_event_schedule)).
4. Filter rows: **`RoundNumber > 0`** and **`EventFormat != 'testing'`** (defense in depth; `OfficialEventName` / testing handling per [Event Schedule Data](https://docs.fastf1.dev/events.html)).
5. Iterate rows in **calendar order** (DataFrame order as returned; optionally sort by `EventDate` if needed).
6. For each row, consider **`Session1DateUtc`…`Session5DateUtc`** (skip `NaT`). Define **next session instant** as the **earliest session time strictly greater than `now_utc`** among sessions that exist for that weekend.
7. **Select the first event** (in order) for which that **earliest future session** exists.
8. If **no** event qualifies for `year`, repeat steps 3–7 for **`year + 1`** (late-season rollover).

**Structured payload (SCHED-01):** at minimum **`EventName`** / **`OfficialEventName`**, **`Country`**, **`Location`** (and/or other columns the plan treats as “circuit identity”), **`EventDate`**, and **per-session UTC** for `Session1`…`Session5` where present (names from `Session1`… columns + `Session*DateUtc`).

### Anti-patterns to avoid

- **Using `datetime.now()`** as authoritative clock when TIME-01 failed without an explicit plan decision to fall back.
- **Relying on `Session*DateUtc` for pre-2018** as exact TV times for FP/Q — docs state assumptions; surface **caveats** in return metadata or docstrings.
- **Registering LangGraph tools** in Phase 17 — out of scope (Phase 18).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| F1 calendar HTTP + parsing | Custom scraper of F1.com | `fastf1.get_event_schedule` | Backends, fallbacks (`fastf1` → `f1timing` → `ergast`), caching |
| Retry/time sync | NTP client in Python | TimeAPI.io + httpx | Requirement names TimeAPI as authority |
| Schedule row shape | Ad-hoc dicts without tests | pandas + explicit column list in tests | FastF1 adds/changes columns by season |

**Key insight:** FastF1 already encodes **Ergast limitations** and **2018 boundary**; the product’s job is to **not over-claim precision** and to **test selection logic** deterministically.

## Common Pitfalls

### Pitfall 1: `include_testing` defaults to True

**What goes wrong:** Testing rows appear even when you filter `EventFormat`.  
**Why:** `get_event_schedule(year)` defaults `include_testing=True`.  
**How to avoid:** Always pass **`include_testing=False`** unless a future phase explicitly needs tests.  
**Warning signs:** Rows with `RoundNumber == 0` or `EventFormat == 'testing'`.

### Pitfall 2: Naive UTC vs timezone-aware comparisons

**What goes wrong:** `TypeError` or wrong ordering mixing aware/naive datetimes.  
**Why:** FastF1 documents **`Session*DateUtc`** as **non-timezone-aware UTC**.  
**How to avoid:** Parse TimeAPI ISO to **UTC naive** or **normalize both** to `pd.Timestamp` with `tz="UTC"` then strip for comparison — pick **one convention** and apply everywhere.

### Pitfall 3: Sprint formats and sparse session columns

**What goes wrong:** Assuming five sessions always exist; `NaT` in unused slots.  
**Why:** Event formats (`sprint`, `sprint_shootout`, `sprint_qualifying`, `conventional`) change session count/names ([docs](https://docs.fastf1.dev/events.html)).  
**How to avoid:** Iterate **only non-null** `Session*DateUtc` columns dynamically.

### Pitfall 4: Ergast / pre-2018 session times

**What goes wrong:** User trusts FP2 time for 2007.  
**Why:** Before 2018 (or `backend='ergast'`), **only race** has a reliable time; other sessions are **derived from a conventional weekend** and may be wrong ([Supported Seasons](https://docs.fastf1.dev/events.html)).  
**How to avoid:** Attach **`schedule_data_quality: "full_2018_plus" | "ergast_limited"`** (or similar) in structured output; document in verification.

### Pitfall 5: httpx timeout type

**What goes wrong:** Hang on connect vs read.  
**Why:** Single float applies to all phases differently by httpx version.  
**How to avoid:** Use **`httpx.Timeout(TIMEAPI_TIMEOUT)`** or explicit connect/read splits if the plan requires it.

## Code Examples

### httpx error mapping (illustrative)

```python
# Pattern only — align with project exception types
import httpx

try:
    r = client.get(url)
    r.raise_for_status()
except httpx.TimeoutException as e:
    raise TimeApiError("timeout", str(e)) from e
except httpx.HTTPStatusError as e:
    raise TimeApiError("http", str(e.response.status_code)) from e
except httpx.RequestError as e:
    raise TimeApiError("network", str(e)) from e
```

### Optional: monkeypatch FastF1 in tests

```python
import pandas as pd

def fake_schedule(year: int):
    return pd.DataFrame([{
        "RoundNumber": 1,
        "Country": "Bahrain",
        "Location": "Sakhir",
        "EventName": "Bahrain",
        "OfficialEventName": "Bahrain Grand Prix",
        "EventFormat": "conventional",
        "EventDate": pd.Timestamp("2026-03-01 00:00:00"),
        "Session1": "Practice 1",
        "Session1DateUtc": pd.Timestamp("2026-02-28 12:00:00"),
        # ...
    }])

monkeypatch.setattr("src.integrations.f1_schedule_service.fastf1.get_event_schedule", fake_schedule)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Local `datetime.utcnow()` for agent “now” | Network time API | Phase 17 | Reduces model/timezone hallucination for “сейчас” |
| Ergast-only calendars | FastF1 multi-backend (`fastf1`, `f1timing`, `ergast` fallback) | FastF1 2.x–3.x | More reliable **2018+** schedules |

**Deprecated/outdated:** `force_ergast=True` → prefer **`backend='ergast'`** per [get_event_schedule](https://docs.fastf1.dev/fastf1.html#get_event_schedule).

## Open Questions

1. **Exact unified JSON schema for `/api/v1/time/current/utc` under all `Accept` headers**  
   - What we know: Probe returned `{"utc_time": "....Z"}`.  
   - What’s unclear: Whether server ever returns full `CurrentTime` object on this path.  
   - Recommendation: Parse **`utc_time`** first; optionally merge with `/unix` for cross-check if plan wants redundancy (still one attempt each unless retry documented).

2. **Whether to expose `Country` only vs `Location` + `OfficialEventName` in the minimal payload**  
   - What we know: SCHED-01 asks for stage name + country/circuit **as FastF1 provides**.  
   - What’s unclear: UI/tool copy preferences.  
   - Recommendation: Include **`EventName`**, **`OfficialEventName`**, **`Country`**, **`Location`** in service model; Phase 18 can trim for prompts.

## Environment Availability

**Step 2.6 executed in research environment (2026-03-28):**

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3 | fastf1, httpx, pytest | ✓ | e.g. 3.14 (research host) | Match project/runtime pin if any |
| httpx | TIME-01 | ✓ | 0.28.1 (requirements) | — |
| fastf1 | SCHED-01 | ✗ (not in venv yet) | — | `pip install` as part of Phase 17 |
| Outbound HTTPS | TimeAPI, FastF1 backends | ✓ (TimeAPI probed) | — | Tests use mocks; CI offline |
| pandas | SCHED-01 | ✓ (via fastf1 install) | — | — |

**Missing dependencies with no fallback:**

- None for **design**; **execution** needs **`fastf1` added to `requirements.txt`**.

**Missing dependencies with fallback:**

- **Live network** in CI → use mocks; optional smoke with env flag locally.

## Validation Architecture

> Nyquist: `workflow.nyquist_validation` is **enabled** in `.planning/config.json`.

### Test framework

| Property | Value |
|----------|-------|
| Framework | pytest ≥8 (`requirements.txt`) |
| Config file | `pytest.ini` (markers only; no per-path addopts beyond `no:lazy-fixture`) |
| Quick run command | `pytest tests/test_timeapi_client.py tests/test_f1_schedule_service.py -x` *(files to be added in Phase 17)* |
| Full suite command | `pytest` |

### Phase requirements → test map

| Req ID | Behavior | Test type | Automated command | File exists? |
|--------|----------|-----------|-------------------|--------------|
| TIME-01 | Success path parses unix + utc JSON | unit | `pytest tests/test_timeapi_client.py -x` | ❌ Wave 0 |
| TIME-01 | Timeout / 5xx / connection → structured error + **fixed RU message** constant | unit | `pytest tests/test_timeapi_client.py::test_timeapi_degraded -x` | ❌ Wave 0 |
| TIME-01 | Single HTTP attempt (no retry unless plan adds) | unit | assert mock transport call count `== 1` | ❌ Wave 0 |
| SCHED-01 | Filters `RoundNumber>0`, excludes testing; picks next event by session > now | unit | `pytest tests/test_f1_schedule_service.py -x` | ❌ Wave 0 |
| SCHED-01 | Year+1 rollover when current year has no future race | unit | DataFrame fixture ending before `now` → loads next year via monkeypatch | ❌ Wave 0 |
| SCHED-01 | Ergast/pre-2018 caveat flag or docstring contract | unit / static | optional `test_schedule_metadata_pre_2018` | ❌ Wave 0 |
| TIME-01 (live) | Real TimeAPI reachable | smoke (opt-in) | `RUN_TIMEAPI_SMOKE=1 pytest tests/test_timeapi_client.py -m timeapi_live -x` | ❌ Wave 0 |

**httpx mocking:** Prefer **`httpx.MockTransport`** or **`unittest.mock.patch`** on `httpx.Client.get` — avoids new dev dependencies. Alternatively **`pytest-httpx`** / **`respx`** if the project later standardizes on them.

**FastF1 mocking:** **`monkeypatch.setattr(fastf1, "get_event_schedule", ...)`** returning a **`pandas.DataFrame`** built inline or loaded from **`tests/fixtures/event_schedule_*.json`** converted to DataFrame in fixture (recorded snapshot optional).

**Sampling rate:**

- **Per task commit:** `pytest tests/test_timeapi_client.py tests/test_f1_schedule_service.py -x`
- **Per wave merge:** `pytest`
- **Phase gate:** full `pytest` green before `/gsd-verify-work`

### Wave 0 gaps

- [ ] `tests/test_timeapi_client.py` — covers TIME-01 (success + failure + RU constant)
- [ ] `tests/test_f1_schedule_service.py` — covers SCHED-01 (filtering, ordering, rollover)
- [ ] `pytest.ini` — add marker `timeapi_live` if opt-in smoke used
- [ ] `fastf1` in `requirements.txt` — install in dev/CI

*(No gaps once above exist and tests pass.)*

## Sources

### Primary (HIGH confidence)

- [TimeAPI OpenAPI](https://www.timeapi.io/swagger/v1/swagger.json) — paths `/api/v1/time/current/unix`, `/api/v1/time/current/utc`
- [FastF1 — Event Schedule Data / Supported Seasons](https://docs.fastf1.dev/events.html) — columns, `RoundNumber`, `EventFormat`, **2018 vs Ergast**, testing support
- [FastF1 — `get_event_schedule`](https://docs.fastf1.dev/fastf1.html#get_event_schedule) — `include_testing`, `backend`

### Secondary (MEDIUM confidence)

- Live HTTP probe `curl https://timeapi.io/api/v1/time/current/{unix,utc}` (2026-03-28) — concrete JSON keys

### Tertiary (LOW confidence)

- GitHub issues discussing schedule backend fallback chains — useful for ops/debugging, not for contract guarantees

## Metadata

**Confidence breakdown:**

- Standard stack: **HIGH** — versions from PyPI + repo pins; APIs from official docs
- Architecture: **HIGH** — aligned with ROADMAP + REQUIREMENTS + `tavily_tool.py` env-timeout pattern
- Pitfalls: **HIGH** — taken verbatim from FastF1 “Supported Seasons”

**Research date:** 2026-03-28  
**Valid until:** ~2026-04-28 (refresh if TimeAPI schema or fastf1 4.x appears)
