---
phase: 03-historical-rag-grounding
plan: 04
subsystem: rag
tags: [chromadb, retrieval, grounding, evidence, testing]
requires:
  - phase: 03-03
    provides: deterministic f1db chunk indexing into f1_historical collection
provides:
  - real Chroma query path over indexed f1db chunks at runtime
  - endpoint-level evidence traceability verification without monkeypatched retrieval
affects: [phase-03-verification, phase-04-ru-qna-answer-reliability]
tech-stack:
  added: [chromadb]
  patterns: [dataset-scoped where filters, seeded integration tests for retrieval contracts]
key-files:
  created: []
  modified:
    - src/retrieval/retriever.py
    - tests/test_rag_grounding.py
    - tests/test_api_async_contracts.py
key-decisions:
  - "Compose Chroma metadata filters with $and to combine dataset and canonical entity constraints."
  - "Verify grounding using seeded local Chroma collection instead of monkeypatching retriever internals."
patterns-established:
  - "Runtime retrieval must target dataset=f1db and collection=f1_historical."
  - "Evidence contract tests should assert source_id/snippet/entity_tags/rank_score/used_in_answer."
requirements-completed: [RAG-01, RAG-03]
duration: 10 min
completed: 2026-03-27
---

# Phase 3 Plan 04: Runtime Grounding Gap Closure Summary

**Replaced simulated retrieval verification with real Chroma-backed f1db retrieval tests and fixed canonical-filter query behavior for runtime grounding.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-27T16:58:00Z
- **Completed:** 2026-03-27T17:08:42Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added seeded-index retriever integration test proving ranked hits come from real Chroma collection data.
- Fixed runtime Chroma filter composition so dataset and canonical entity constraints can be queried together.
- Added async contract test that verifies `/next_message` returns traceable non-empty evidence without monkeypatched retrieval.

## Task Commits

Each task was committed atomically:

1. **Task 1: Replace simulated retrieval with real indexed-chunk Chroma query** - `95df7e8` (fix)
2. **Task 2: Validate endpoint grounding and evidence linkage against real retrieval path** - `e6992e3` (test)

## Files Created/Modified
- `src/retrieval/retriever.py` - fixes Chroma `where` filter shape to keep f1db scope and canonical filters valid in runtime queries.
- `tests/test_rag_grounding.py` - adds seeded-index retriever assertion and grounded `/next_message` behavior test from real collection data.
- `tests/test_api_async_contracts.py` - adds non-mocked evidence traceability contract test using seeded `f1_historical` data.

## Decisions Made
- Used Chroma `$and` metadata filter composition because Chroma query validation requires a single top-level operator when combining constraints.
- Kept retrieval integration deterministic by seeding local `.chroma` test data with explicit `dataset`, `canonical_entity_id`, and `source_id` metadata.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed missing `chromadb` dependency**
- **Found during:** Task 1
- **Issue:** Tests could not import `chromadb`, blocking real retrieval execution.
- **Fix:** Installed `chromadb` via `python3 -m pip install chromadb`.
- **Files modified:** Environment packages (no tracked repo files)
- **Verification:** `pytest tests/test_rag_grounding.py::test_retriever_returns_ranked_hits_from_seeded_index -q`
- **Committed in:** `95df7e8`

**2. [Rule 1 - Bug] Fixed invalid Chroma combined metadata filter**
- **Found during:** Task 1
- **Issue:** Query failed because `where` had multiple top-level keys instead of one operator.
- **Fix:** Changed filter to `$and` with `dataset=f1db` and canonical `$in` clause.
- **Files modified:** `src/retrieval/retriever.py`
- **Verification:** `pytest tests/test_rag_grounding.py::test_retriever_returns_ranked_hits_from_seeded_index -q`
- **Committed in:** `95df7e8`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes were required for correctness and execution; no scope creep introduced.

## Known Stubs
None.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Runtime grounding now exercises real Chroma retrieval against `f1db`-scoped metadata and returns traceable evidence payloads.
- Ready for Phase 3 closure verification and onward Phase 4 planning.

---
*Phase: 03-historical-rag-grounding*
*Completed: 2026-03-27*

## Self-Check: PASSED

- Found `.planning/phases/03-historical-rag-grounding/03-04-SUMMARY.md`.
- Found task commits `95df7e8` and `e6992e3` in git history.
