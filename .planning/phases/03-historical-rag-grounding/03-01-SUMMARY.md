---
phase: 03-historical-rag-grounding
plan: 01
subsystem: api
tags: [rag, chromadb, retrieval, pydantic, pytest]
requires:
  - phase: 02-async-backend-contracts
    provides: typed async API contracts and deterministic response patterns
provides:
  - Dictionary-first RU/EN alias normalization and canonical mapping
  - Deterministic retrieval defaults with explicit f1db-only scope guard
  - Typed evidence contracts and formatter for downstream synthesis
affects: [03-02-next-message-grounding, rag-traceability, ru-en-query-matching]
tech-stack:
  added: []
  patterns: [dictionary-first aliasing, deterministic retrieval defaults, evidence-first contracts]
key-files:
  created:
    - src/retrieval/__init__.py
    - src/retrieval/retriever.py
    - src/retrieval/evidence.py
    - src/retrieval/alias_resolver.py
    - tests/test_alias_resolution.py
    - pytest.ini
  modified:
    - src/models/api_contracts.py
key-decisions:
  - Keep retrieval historical-only with explicit dataset f1db scope guard in this plan.
  - Use strict normalized dictionary matching for RU/EN aliases and avoid fuzzy decision paths.
  - Disable incompatible pytest lazy-fixture plugin locally to unblock deterministic test execution.
patterns-established:
  - "Alias resolver returns (normalized_query, canonical_entity_ids, entity_tags) as the retrieval handoff shape."
  - "Evidence formatter enforces bounded snippet length and stable trace fields."
requirements-completed: [RAG-01, RAG-02]
duration: 2 min
completed: 2026-03-27
---

# Phase 03 Plan 01: Retrieval foundation Summary

**Dictionary-first RU/EN entity resolution, deterministic historical retrieval defaults, and typed evidence formatting were implemented as the Phase 3 grounding foundation.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-27T15:44:39Z
- **Completed:** 2026-03-27T15:46:49Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added `EvidenceItem` and `RetrievalArtifacts` for typed evidence contracts.
- Implemented retrieval primitives with deterministic defaults (`top_k=5`, `min_score=0.35`) and explicit historical scope.
- Implemented RU/EN alias resolver with normalized exact dictionary matching and parity tests.

## Task Commits

Each task was committed atomically:

1. **Task 1: Define retrieval contracts and deterministic defaults** - `bc489e4` (test), `47bce30` (feat)
2. **Task 2: Implement dictionary-first RU/EN alias resolver** - `8fa62ca` (test), `37d16f5` (feat)

**Plan metadata:** `(pending docs commit)`

## Files Created/Modified
- `src/models/api_contracts.py` - Adds `EvidenceItem` and `RetrievalArtifacts`.
- `src/retrieval/retriever.py` - Adds deterministic historical retrieval API and f1db scope guard.
- `src/retrieval/evidence.py` - Adds evidence formatter with 280-char snippet truncation.
- `src/retrieval/alias_resolver.py` - Adds normalized dictionary-first RU/EN alias mapping.
- `tests/test_alias_resolution.py` - Adds retrieval contract and RU/EN alias parity tests.
- `pytest.ini` - Disables incompatible global plugin causing pytest collection failures.

## Decisions Made
- Retrieval remains historical-only in this plan; live API paths remain out of scope for Phase 5.
- Alias matching is deterministic and dictionary-first, with normalization only and no fuzzy lookup.
- `resolve_entities` contract was standardized to return normalized text plus canonical IDs/tags for downstream retriever usage.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Disabled incompatible pytest plugin to unblock test execution**
- **Found during:** Task 2 (Implement dictionary-first RU/EN alias resolver)
- **Issue:** External `pytest_lazyfixture` plugin crashed collection under current pytest runtime, blocking required verification command.
- **Fix:** Added `pytest.ini` with `-p no:lazy-fixture` to disable the incompatible plugin for this repository.
- **Files modified:** `pytest.ini`
- **Verification:** `pytest tests/test_alias_resolution.py -q` exits 0.
- **Committed in:** `37d16f5` (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Blocking fix was required for deterministic verification and did not change retrieval scope.

## Known Stubs
- `src/retrieval/retriever.py`: `_query_historical_index` currently returns from `simulated_hits` placeholder list; real Chroma query integration is deferred to the next plan where `/next_message` wiring is implemented.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Retrieval primitives and alias normalization contracts are ready for inline `/next_message` integration in `03-02`.
- No blockers remain for proceeding to evidence-to-answer linkage work.

## Self-Check: PASSED
- Found `.planning/phases/03-historical-rag-grounding/03-01-SUMMARY.md`.
- Found task commits `bc489e4`, `47bce30`, `8fa62ca`, and `37d16f5` in `git log`.

---
*Phase: 03-historical-rag-grounding*
*Completed: 2026-03-27*
