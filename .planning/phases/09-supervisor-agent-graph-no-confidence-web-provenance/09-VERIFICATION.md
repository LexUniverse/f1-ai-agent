---
status: passed
phase: 09-supervisor-agent-graph-no-confidence-web-provenance
updated: 2026-03-28
---

# Phase 9 Verification

## Must-haves

| Criterion | Evidence |
|-----------|----------|
| Supervisor decides on full candidate vs user question | `gigachat_supervisor_accept_answer` + `_node_supervisor` in `f1_turn_graph.py` |
| RAG first; ≤2 Tavily after reject | `web_search_rounds` cap + routing in `f1_turn_graph.py` |
| AGT-05 terminal message | `UNABLE_TO_ANSWER_SUPERVISOR_RU` in `finalize_fail`; tests `test_two_tavily_then_agt05` |
| No confidence in API / graph contract | `rg confidence` empty in `gigachat_rag.py`, `f1_turn_graph.py`, `chat.py`; contract tests |
| `details.web` when web used | `assemble_next_message_details` + `WebSearchDetails`; `test_next_message_contract_phase9.py` |

## Automated

- `python3 -m pytest tests/ -q --ignore-glob='*integration*'` — 60 passed (2026-03-28).

## human_verification

_None required for merge; optional: hit `/next_message` with TAVILY_API_KEY set and confirm `details.web` in browser/network tab._
