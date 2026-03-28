---
gsd_state_version: 1.0
milestone: v1.6
milestone_name: Real-time clock & F1 schedule tools
status: executing
last_updated: "2026-03-28T12:00:00.000Z"
last_activity: 2026-03-28
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 2
  completed_plans: 2
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` — **Current milestone: v1.6** (phases **17–19**). **v1.5** закрыт частично (**15** skipped, docs → **19**).

## Current Position

Phase: 18
Plan: Not started
Status: Phase 17 complete — next: Phase 18 (worker tools)
Last activity: 2026-03-28

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
Next: `/gsd-discuss-phase 18` or `/gsd-plan-phase 18` (TOOL-01 worker tools)
