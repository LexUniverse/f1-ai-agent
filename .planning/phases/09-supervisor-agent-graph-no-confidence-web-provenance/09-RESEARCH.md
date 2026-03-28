# Phase 9 — Technical Research

**Phase:** 9 — Supervisor–Agent Graph, No Confidence, Web Provenance  
**Question:** What do we need to know to implement the supervisor loop, LangChain tool binding, and API changes?

## Summary

- **LangGraph:** Model the loop as **explicit nodes** (retrieve → `agent1_rag` → `supervisor` → conditional → optional `invoke_tavily` → `agent1_with_web` → `supervisor` again) rather than a black-box ReAct agent, so **AGT-04** search caps are **deterministic** in code.
- **LangChain:** Wrap **`run_tavily_search_once`** with **`langchain_core.tools.tool`** or **`StructuredTool`**, pass to an Agent 1 “tool-capable” step — or **manually** call the tool from a node when supervisor requests web (simpler, fewer hidden loops). **Recommendation:** **manual node** calls Tavily when supervisor rejects, to keep **exactly 2** invocations enforceable without agent autonomy bugs.
- **Supervisor prompt:** Judge **candidate answer text** vs **user question**; require JSON. Reuse `_chat_completion_json` pattern with a new system prompt distinct from sufficiency judge.
- **API-05:** `details` becomes free of `confidence`; add **`details.web`**: `{"queries": [...], "results": [{"url", "title", "content_snippet"}]}` (shape fixed in `api_contracts` or typed dict in plan).
- **Tests:** Mock GigaChat responses for supervisor accept/reject sequences; mock Tavily; assert state transitions and final message (including AGT-05).

## Risks

- **Latency:** Multiple GigaChat round-trips per turn — document env timeouts; consider single supervisor model with strict JSON.
- **False rejects:** Supervisor may over-reject RAG — mitigate with clear prompt (“accept if question is directly answered”).

## Validation Architecture

Phase 9 validation uses **pytest** (existing project standard).

| Dimension | Approach |
|-----------|----------|
| **Automated graph** | `tests/test_f1_supervisor_graph.py` (new): mock `gigachat_rag` supervisor + worker functions; mock `run_tavily_search_once`; assert `web_search_rounds` ≤ 2 and terminal `out_message` for AGT-05 path. |
| **API contract** | `tests/test_chat_contracts.py` or extend existing API tests: JSON response from `/next_message` (mocked backend) **must not** contain `"confidence"` key in `details`; when web used, `details.web` present. |
| **Regression** | Run full offline suite: `python -m pytest tests/ -q` excluding integration marker. |

**Quick command after each task:** `python -m pytest tests/test_f1_supervisor_graph.py -q` (once file exists) or targeted file from plan.

**Full suite:** `python -m pytest tests/ -q`

---

## RESEARCH COMPLETE
