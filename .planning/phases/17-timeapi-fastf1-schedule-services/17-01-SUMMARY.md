---
phase: 17-timeapi-fastf1-schedule-services
plan: 01
subsystem: api
tags: [httpx, timeapi, pydantic]

requires:
  - phase: 14
    provides: RAG baseline (unchanged)
provides:
  - Authoritative unix/naive-UTC «now» via TimeAPI single GET
  - TimeApiError + fixed RU degraded string for Phase 18 tools
affects:
  - phase 18 worker tools

tech-stack:
  added: []
  patterns: [env TIMEAPI_TIMEOUT default 10; no httpx retries on success path]

key-files:
  created:
    - src/integrations/messages_ru.py
    - src/integrations/timeapi_client.py
    - tests/test_timeapi_client.py
  modified:
    - pytest.ini

key-decisions:
  - "Derive UTC display only from unix endpoint (no second /utc call)."

patterns-established:
  - "Integration errors use small exception types + leaf messages_ru module."

requirements-completed: [TIME-01]

duration: 25min
completed: 2026-03-28
---

# Phase 17 Plan 01 Summary

**httpx TimeAPI client: one GET to `/time/current/unix`, `TimeApiNow`, `TimeApiError`, and `TIMEAPI_UNAVAILABLE_MESSAGE_RU` with mocked unit tests.**

## Performance

- **Tasks:** 2
- **Completed:** 2026-03-28

## Accomplishments

- Fixed Russian degraded copy and `degraded_message_ru()` helper for callers.
- `fetch_timeapi_now()` maps timeout/HTTP/network/parse failures to structured `TimeApiError`.
- `pytest` coverage for success (single call), timeout, HTTP error, parse errors; opt-in `timeapi_live` marker.

## Files Created/Modified

- `src/integrations/messages_ru.py` — `TIMEAPI_UNAVAILABLE_MESSAGE_RU`
- `src/integrations/timeapi_client.py` — client + models
- `tests/test_timeapi_client.py` — MockTransport / patches
- `pytest.ini` — `timeapi_live` marker

## Deviations from Plan

None — plan executed as written.

## Next Phase Readiness

- TIME-01 clock ready for `f1_schedule_service` (plan 02) and Phase 18 tools.

## Self-Check: PASSED

- Key files exist; `pytest tests/test_timeapi_client.py` green.
