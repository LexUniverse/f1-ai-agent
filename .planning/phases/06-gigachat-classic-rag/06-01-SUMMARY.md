---
phase: 06-gigachat-classic-rag
plan: 01
subsystem: api
tags: [gigachat, rag, fastapi, pydantic]

requires:
  - phase: 05-live-enrichment
    provides: LiveDetails on live path, summarize_live_next_payload_ru
provides:
  - src/answer/gigachat_rag.py primary sync GigaChat completion with hybrid StructuredRUAnswer
  - /next_message historical and live success branches call gigachat_synthesize_* with template fallback on exception (silent metadata until plan 02)
affects: [phase-07-streamlit]

tech-stack:
  added: [gigachat==0.2.0]
  patterns: [Hybrid RAG — LLM sections + deterministic sources_block_ru and confidence from retrieval helpers]

key-files:
  created: [requirements.txt, src/answer/gigachat_rag.py, tests/test_gigachat_rag.py]
  modified: [src/answer/russian_qna.py, src/api/chat.py, tests/test_qna_reliability.py, tests/test_live_enrichment.py, tests/test_api_async_contracts.py, tests/test_rag_grounding.py]

key-decisions:
  - "JSON envelope from model validated via Pydantic; one repair round then re-raise for chat-layer fallback."
  - "Per-request GigaChat context manager with env-driven timeout, retries, SSL verify."

patterns-established:
  - "Monkeypatch src.api.chat.gigachat_synthesize_* in tests to avoid real GigaChat network calls."

requirements-completed: [GC-01, GC-03]

duration: 45min
completed: 2026-03-27
---

# Phase 6: GigaChat Classic RAG — Plan 01 Summary

**Hybrid GigaChat RAG module with enumerated evidence prompts, deterministic citations, and chat orchestration that falls back to legacy RU template builders when the SDK or parsing fails.**

## Performance

- **Duration:** ~45 min
- **Tasks:** 4
- **Files modified:** 9

## Accomplishments

- `build_sources_block_ru_from_evidence` deduplicates citation formatting for templates and GigaChat assembly.
- `gigachat_rag.py` implements historical and live synthesis with `GIGACHAT_SUCCESS_ROUTE` metadata on success paths.
- Integration tests mock GigaChat entrypoints across API and RAG suites.

## Task Commits

Single consolidated commit for plan 01 implementation (orchestrated inline).

## Files Created/Modified

- `requirements.txt` — pin `gigachat==0.2.0`
- `src/answer/gigachat_rag.py` — GigaChat client, prompts, JSON parse/repair
- `src/answer/russian_qna.py` — shared sources block helper
- `src/api/chat.py` — try GigaChat then template fallback
- `tests/test_gigachat_rag.py` — unit and API synthesis route tests
- Additional test files — monkeypatches for `gigachat_synthesize_*`

## Deviations from Plan

Wave 1 shipped with GC-02 disclosure and `template_fallback` synthesis metadata in the same pass as Plan 02 because both touch identical `chat.py` except branches; Plan 02 tasks were completed immediately after Plan 01 in one execution run.

## Issues Encountered

None.

## Next Phase Readiness

Plan 02 artifacts (fallback disclosure constants and tests) delivered in same session; phase verification covers full GC-01–GC-03.

---
*Phase: 06-gigachat-classic-rag · Plan 01*
*Completed: 2026-03-27*
