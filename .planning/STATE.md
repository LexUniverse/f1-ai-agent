---
gsd_state_version: 1.0
milestone: v1.6
milestone_name: Real-time clock & F1 schedule tools
status: Roadmap ready — plan Phase 17
last_updated: "2026-03-28T14:00:00.000Z"
last_activity: 2026-03-28
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` — **Current milestone: v1.6** (TimeAPI.io + FastF1 schedule tools). **v1.5** phases 15–16 remain on `.planning/ROADMAP.md` until shipped.

## Current Position

Phase: **17** — TimeAPI & FastF1 schedule services (**TIME-01**, **SCHED-01**) — **planned** (first v1.6 execution target after roadmap)
Plan: —
Status: Roadmap updated; next step `/gsd-plan-phase 17` (or complete **v1.5** phases **15–16** first if following strict milestone order on `.planning/ROADMAP.md`)
Last activity: 2026-03-28 — v1.6 phases **17–18** appended to ROADMAP

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
