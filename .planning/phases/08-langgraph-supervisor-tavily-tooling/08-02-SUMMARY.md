---
phase: 08-langgraph-supervisor-tavily-tooling
plan: 02
subsystem: api
tags: [langgraph, tavily, gigachat, fastapi, asyncio]

requires:
  - phase: 08-langgraph-supervisor-tavily-tooling
    provides: 08-01 graph skeleton
provides:
  - async /next_message with asyncio.to_thread(run_f1_turn_sync)
  - GigaChat Tavily query author + web synthesis with URL sources_block_ru
  - WEB_SEARCH_UNAVAILABLE + fixed RU copy
  - f1api client and live branches removed from src
affects: [09, 10]

tech-stack:
  added: []
  patterns: [thread offload for sync LangGraph from async route]

key-files:
  created:
    - src/search/messages_ru.py
    - tests/test_tavily_turn.py
  modified:
    - src/api/chat.py
    - src/answer/gigachat_rag.py
    - src/graph/f1_turn_graph.py
    - src/main.py
    - streamlit_app.py
    - tests/conftest.py
  deleted:
    - src/integrations/f1api_client.py
    - tests/test_f1api_client.py
    - tests/test_live_enrichment.py

key-decisions:
  - "Chroma integration tests patch graph retrieve with score boost so weak embeddings still exercise RAG path."
  - "Chat merges full synthesis dict from graph out_details (route + gigachat_error_class)."

patterns-established:
  - "Monkeypatch src.graph.f1_turn_graph for API tests that previously patched chat.retrieve/gigachat."

requirements-completed: [AGT-01, AGT-02, SRCH-01, SRCH-02]

duration: 45min
completed: 2026-03-28
---

# Phase 8 plan 02 — API wiring & f1api removal

**Async `/next_message` runs the compiled LangGraph in a worker thread; Tavily failures return `WEB_SEARCH_UNAVAILABLE` with stable Russian copy; f1api client and live Streamlit panel removed.**

## Performance

- **Duration:** ~45 min
- **Tasks:** 3

## Accomplishments

- `gigachat_author_tavily_query`, `gigachat_synthesize_from_web_results`, `gigachat_judge_rag_sufficient`; removed f1api/live synthesis entry points from `gigachat_rag.py`
- Real RAG and web synthesis nodes in `f1_turn_graph.py` with template fallbacks
- Test suite migrated: `test_tavily_turn.py`, graph-level patches, boosted Chroma scores for two grounding tests

## Task commits

Single commit for plans 08-02 deliverables (post 08-01 commit).

## Deviations

None material — README still mentions f1api (Phase 10 DOC scope per plan).

## Next phase readiness

Phase 9 can add `details.web` / Streamlit web panels per roadmap.

---
*Phase: 08-langgraph-supervisor-tavily-tooling*
*Completed: 2026-03-28*
