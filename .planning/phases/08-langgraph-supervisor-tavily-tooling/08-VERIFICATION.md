---
status: passed
phase: 08-langgraph-supervisor-tavily-tooling
completed: 2026-03-28
---

# Phase 8 Verification — LangGraph supervisor & Tavily

## Goal (from ROADMAP)

**GigaChat** supervises **RAG** and **Tavily** with an explicit sufficiency gate; **f1api** removed from the answering path; web citations in `sources_block_ru` when Tavily contributes.

## Requirements traceability

| ID      | Verified |
|---------|----------|
| AGT-01  | Yes — `src/graph/f1_turn_graph.py` compiled graph; `run_f1_turn_sync`; `asyncio.to_thread` in `src/api/chat.py` |
| AGT-02  | Yes — hybrid sufficiency + single Tavily call + `WEB_SEARCH_UNAVAILABLE` on tool/config/empty results |
| SRCH-01 | Yes — `gigachat_synthesize_from_web_results` builds `sources_block_ru` with URLs; test `test_gigachat_synthesize_from_web_results_sources_contain_url` |
| SRCH-02 | Yes — no `F1ApiClient` / `f1api_client` under `src/`; client file deleted |

## Must-haves (spot-check)

- `src/search/messages_ru.py` exports `WEB_SEARCH_UNAVAILABLE_MESSAGE_RU`
- `rg`-style: no `f1_api_client` or `F1ApiClient` in `src/`
- `tests/test_tavily_turn.py` asserts stable degraded message and code

## Automated checks

```bash
python3 -m pytest tests/ -q
```

Result: **54 passed** (2026-03-28).

## human_verification

None required for phase close — real Tavily/GigaChat E2E deferred to Phase 10 per 08-VALIDATION.

## Gaps

None.
