---
phase: 08-langgraph-supervisor-tavily-tooling
plan: 01
subsystem: api
tags: [langgraph, langchain, tavily, rag, pytest]

requires:
  - phase: 07-streamlit-ui-local-run
    provides: prior API and UI contracts
provides:
  - compiled LangGraph turn with retrieve, sufficiency gate, single Tavily hop, stub synthesis
  - TavilySearchResults wrapper with TAVILY_TIMEOUT
  - offline routing tests
affects: [08-02]

tech-stack:
  added: [langgraph, langchain-core, langchain-community]
  patterns: [sync graph.invoke, injectable judge_fn for borderline RAG]

key-files:
  created:
    - src/graph/f1_turn_graph.py
    - src/graph/tavily_tool.py
    - tests/test_f1_assistant_graph.py
  modified:
    - requirements.txt
    - src/graph/__init__.py

key-decisions:
  - "Subclass TavilySearchAPIWrapper to pass requests timeout for TAVILY_TIMEOUT."
  - "Default judge raises NotImplementedError; production injects real judge in 08-02."

patterns-established:
  - "top_score = max hit score from retrieve_historical_context (same as retriever formula)."

requirements-completed: [AGT-01, AGT-02]

duration: 25min
completed: 2026-03-28
---

# Phase 8: LangGraph skeleton (plan 01)

**Compiled StateGraph with hybrid RAG sufficiency (0.45 pass, 0.35–0.45 judge band), one Tavily call on insufficient path, and pytest mocks proving routes.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- LangGraph nodes: retrieve → sufficiency → tavily or RAG stub → web stub or END on failure
- Tavily tool with TavilyConfigError and HTTP timeout via LangChain Community
- Three offline tests without TAVILY_API_KEY

## Task Commits

1. **Tasks 1–3 (combined)** — single commit (package + graph + tests)

## Files Created/Modified

- `requirements.txt` — langgraph, langchain-core, langchain-community pins
- `src/graph/__init__.py` — exports
- `src/graph/tavily_tool.py` — run_tavily_search_once, TavilyConfigError
- `src/graph/f1_turn_graph.py` — graph build and run_f1_turn_sync
- `tests/test_f1_assistant_graph.py` — routing tests

## Deviations from Plan

None — plan executed as written.

## Issues Encountered

None.

## Next Phase readiness

Ready for 08-02: wire chat.py, real GigaChat synthesis, remove f1api.

---
*Phase: 08-langgraph-supervisor-tavily-tooling*
*Completed: 2026-03-28*
