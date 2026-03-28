---
gsd_state_version: 1.0
milestone: v1.6
milestone_name: Real-time clock & F1 schedule tools
status: Roadmap ready — plan Phase 17
last_updated: "2026-03-28T15:00:00.000Z"
last_activity: 2026-03-28
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` — **Current milestone: v1.6** (phases **17–19**). **v1.5** закрыт частично (**15** skipped, docs → **19**).

## Current Position

Phase: **17** — TimeAPI & FastF1 schedule services (**TIME-01**, **SCHED-01**) — **planned** (первый шаг v1.6; **не** ждём Phase 15)
Plan: —
Status: Roadmap: **15** skipped; **16** → **19**; next `/gsd-plan-phase 17`
Last activity: 2026-03-28 — roadmap reprioritized (время/расписание раньше доков)

## Performance Metrics

_Not measured._

## Accumulated Context

### Decisions

- **v1.3:** Supervisor judges answers; Agent 1 RAG-first; Tavily capped; `confidence` removed (**API-05**).
- **v1.4:** **One** Tavily call per turn after RAG reject; deepen via **URL choice + titles + optional fetch**; Streamlit **single** provenance expander including **RAG context**.
- **v1.6:** «Сейчас» для логики «следующая гонка» — **TimeAPI.io**; календарь — **FastF1** `EventSchedule`, сравнение с UTC-меткой с TimeAPI.

### Pending Todos

_None._

### Blockers/Concerns

- **v1.5** UAT items (RAG/supervisor) may still apply until Phase 15–16 complete.

## Session Continuity

Last session: 2026-03-28
Next: `/gsd-plan-phase 17` (then **18**); if finishing v1.5 first, `/gsd-plan-phase 15` or **16**
