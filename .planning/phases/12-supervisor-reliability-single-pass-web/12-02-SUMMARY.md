---
phase: 12-supervisor-reliability-single-pass-web
plan: 02
subsystem: api
tags: [pydantic, provenance, fastapi]

requires:
  - phase: 12-supervisor-reliability-single-pass-web
    provides: graph state keys for fetch metadata, finalize details shape
provides:
  - details.provenance (rag, optional web+fetch, synthesis) validated in chat layer
  - ProvenanceSnapshot Pydantic models for API documentation
affects: [13-streamlit-provenance-ui]

tech-stack:
  added: []
  patterns: [model_validate provenance then model_dump into details]

key-files:
  created:
    - tests/test_phase12_provenance.py
  modified:
    - src/models/api_contracts.py
    - src/api/chat.py
    - src/graph/f1_turn_graph.py

key-decisions:
  - "Legacy details.evidence, structured_answer, web unchanged; provenance is additive."

patterns-established:
  - "_build_provenance_snapshot in graph finalize nodes; assemble_next_message_details copies validated provenance."

requirements-completed: [WEB-02]

duration: 0min
completed: 2026-03-28
---

# Phase 12 Wave 2 Summary

**Unified `provenance` on graph finalize and `/next_message` details, with Pydantic typing and Phase 9 field compatibility preserved.**

## Performance

- **Tasks:** 4
- **Files modified:** see frontmatter

## Accomplishments

- `ProvenanceSnapshot`, `ProvenanceRag`, `ProvenanceWeb`, `ProvenanceWebFetch` in `api_contracts.py`.
- `_build_provenance_snapshot` attaches `provenance` on accept and fail finalizers.
- `assemble_next_message_details` validates and passes through `provenance`; no `confidence` string added.
- `tests/test_phase12_provenance.py` asserts JSON contains `provenance`, not `confidence`.

## Task Commits

Inline execution: see session note in 12-01-SUMMARY.

## Deviations from Plan

None.

## Issues Encountered

None.

## Next Phase Readiness

Phase 13 Streamlit can read `details["provenance"]` first.

---
*Phase: 12-supervisor-reliability-single-pass-web / plan 02*
*Completed: 2026-03-28*
