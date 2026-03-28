---
status: passed
phase: 17-timeapi-fastf1-schedule-services
updated: 2026-03-28
---

# Phase 17 Verification

## Must-haves (ROADMAP)

| Criterion | Evidence |
|-----------|----------|
| TIME-01: bounded TimeAPI GET, timeout, RU degraded, no silent local clock | `timeapi_client.py`, `messages_ru.py`, `tests/test_timeapi_client.py` |
| SCHED-01: next GP vs TimeAPI now, RoundNumber>0, non-testing, rollover | `f1_schedule_service.py`, `tests/test_f1_schedule_service.py` |
| Payload: naming, country/location, EventDate, sessions UTC | `NextGrandPrixSchedule` fields + tests |
| Ergast / pre-2018 documented; `schedule_data_quality` | Module docstring + `ergast_limited` for year<2018 |
| fastf1 pin; exports on `src.integrations` | `requirements.txt`, `__init__.py` |

## Requirement IDs

- **TIME-01** — plan 17-01 frontmatter
- **SCHED-01** — plan 17-02 frontmatter

## Automated

- `python3 -m pytest tests/test_timeapi_client.py tests/test_f1_schedule_service.py -q` — pass
- `python3 -m pytest tests/ -q` — full suite pass (2026-03-28)

## human_verification

_None required — behavior covered by mocked unit tests; optional live TimeAPI via `RUN_TIMEAPI_SMOKE=1` + `timeapi_live`._
