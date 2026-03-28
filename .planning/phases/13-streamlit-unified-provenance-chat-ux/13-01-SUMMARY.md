---
phase: 13-streamlit-unified-provenance-chat-ux
plan: 01
subsystem: ui
tags: [streamlit, provenance, pytest]

requires:
  - phase: 12-supervisor-reliability-single-pass-web
    provides: details["provenance"] shape and API assembly
provides:
  - Chronological chat transcript via append (UI-04)
  - Single «Происхождение ответа» expander with RAG / web / synthesis subsections (UI-06)
  - Answer body before expanders; Russian «Актуальные данные (live)» (UI-05, D-07)
  - Pure provenance predicates in src/ui/provenance_display.py with unit tests
affects:
  - phase-14-readme-smokes

tech-stack:
  added: []
  patterns:
    - "Unified vs legacy branching in _render_assistant_block via use_unified_provenance_expander"

key-files:
  created:
    - src/ui/provenance_display.py
    - tests/test_provenance_display.py
  modified:
    - streamlit_app.py

key-decisions:
  - "Legacy Источники / Веб-поиск JSON / Синтез expanders kept only when provenance is not usable"

patterns-established:
  - "Streamlit imports provenance helpers from src.ui without pulling streamlit into pure module"

requirements-completed: [UI-04, UI-05, UI-06]

duration: 25min
completed: 2026-03-28
---

# Phase 13: Streamlit Unified Provenance & Chat UX — Plan 01 Summary

**Chronological chat history, answer-first layout, and one Russian provenance expander (RAG + web + synthesis) with legacy fallback and separate live JSON panel.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Replaced `insert(0, …)` with paired `append` for user then assistant on successful send.
- Added `provenance_display` helpers and tests for unified-provenance detection.
- Refactored `_render_assistant_block` to render unified expander or legacy blocks; renamed live expander to Russian label.

## Task Commits

1. **Task 1: Chronological message list (UI-04)** — `5c198a9`
2. **Task 2: Pure provenance helpers + unit tests** — `72d71ec`
3. **Task 3: Streamlit unified expander + live label** — `a54296c`

## Files Created/Modified

- `streamlit_app.py` — append order; unified vs legacy assistant details rendering.
- `src/ui/provenance_display.py` — `use_unified_provenance_expander`, section markdown builders.
- `tests/test_provenance_display.py` — predicate coverage.

## Deviations from Plan

None — plan executed as written.

## Issues Encountered

None.

## Next Phase Readiness

Ready for Phase 14 (README and credential smokes).

---
*Phase: 13-streamlit-unified-provenance-chat-ux*  
*Completed: 2026-03-28*
