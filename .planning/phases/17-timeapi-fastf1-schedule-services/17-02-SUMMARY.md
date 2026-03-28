---
phase: 17-timeapi-fastf1-schedule-services
plan: 02
subsystem: api
tags: [fastf1, pandas, pydantic]

requires:
  - phase: 17 plan 01
    provides: fetch_timeapi_now / TimeApiNow
provides:
  - resolve_next_grand_prix_schedule vs TimeAPI instant
  - NextGrandPrixSchedule + schedule_data_quality + Ergast/pre-2018 docstrings
affects:
  - phase 18 LangGraph tools

tech-stack:
  added: [fastf1>=3.8.0,<4]
  patterns: [monkeypatched get_event_schedule in tests; year rollover]

key-files:
  created:
    - src/integrations/f1_schedule_service.py
    - tests/test_f1_schedule_service.py
  modified:
    - requirements.txt
    - src/integrations/__init__.py

key-decisions:
  - "schedule_data_quality ergast_limited when loaded season year < 2018."

patterns-established:
  - "Schedule rows filtered RoundNumber>0 and EventFormat!=testing; include_testing=False always."

requirements-completed: [SCHED-01]

duration: 35min
completed: 2026-03-28
---

# Phase 17 Plan 02 Summary

**FastF1 `get_event_schedule` resolver: next non-testing GP with earliest future Session*DateUtc after TimeAPI now, year rollover, Pydantic payload, and package exports.**

## Performance

- **Tasks:** 2
- **Completed:** 2026-03-28

## Accomplishments

- `resolve_next_grand_prix_schedule(season_year=None|int)` with documented Ergast/2018 caveats.
- Deterministic tests via monkeypatch on `fastf1.get_event_schedule` and `fetch_timeapi_now`.
- `src/integrations/__all__` lists public names for Phase 18.

## Files Created/Modified

- `src/integrations/f1_schedule_service.py` — resolver + models
- `tests/test_f1_schedule_service.py`
- `requirements.txt` — fastf1 pin
- `src/integrations/__init__.py` — re-exports

## Deviations from Plan

None — plan executed as written.

## Next Phase Readiness

- SCHED-01 service surface exported; ready for TOOL-01 in Phase 18.

## Self-Check: PASSED

- `pytest tests/test_timeapi_client.py tests/test_f1_schedule_service.py` green; key-links verified for plan 02.
