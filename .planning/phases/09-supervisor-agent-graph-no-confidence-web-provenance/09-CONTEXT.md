# Phase 9: Supervisor–Agent Graph — Context

**Gathered:** 2026-03-28  
**Status:** Ready for planning  
**Source:** Roadmap + REQUIREMENTS.md (no separate discuss-phase; scope locked in milestone replan)

<domain>

## Phase boundary

Deliverables for this phase only:

- Replace the **linear** Phase-8 graph with a **supervisor + Agent 1** loop (**LangGraph** + **LangChain** tool for Tavily).
- **Agent 1** first answers **RAG-only** (no web tool).
- **Supervisor** (GigaChat structured JSON) judges whether the candidate **answers the user’s original question**.
- On reject: Agent 1 may invoke **Tavily** (LangChain-bound tool), re-synthesize; repeat up to **2** total Tavily invocations after the initial RAG attempt.
- If still rejected after the **second** web-backed answer → return fixed **`AGT-05`** Russian message (constant in codebase).
- **API-05:** Remove **`confidence`** from all `/next_message` payloads and from `out_details` assembly.
- **WEB-01:** Populate **`details.web`** when search contributed (queries, URLs, snippets/titles).

Streamlit layout (UI-04/05) is **Phase 10**, not this phase.

</domain>

<decisions>

## Implementation decisions (locked)

- **D-01:** Supervisor output is **machine-parseable** (e.g. JSON `{"accept": true}` or `{"accept": false, "reason": "..."}`) via existing GigaChat JSON completion pattern in `gigachat_rag.py`.
- **D-02:** **Search round counter** in graph state: `web_search_rounds: int`, starts at **0**, incremented **once per successful Tavily invocation** after RAG-only candidate. **Cap at 2** further attempts after RAG (i.e. at most **2** Tavily calls per turn).
- **D-03:** **AGT-05** copy: use module **`src/search/messages_ru.py`** constant **`UNABLE_TO_ANSWER_SUPERVISOR_RU`** (exact string defined in implementation task).
- **D-04:** **LangChain** exposes Tavily as **`StructuredTool`** or **`@tool`** wrapping existing **`run_tavily_search_once`** from `tavily_tool.py` (no duplicate HTTP client).
- **D-05:** **RAG retrieval** remains a **graph node** before Agent 1 RAG synthesis (reuse `retrieve_historical_context` / `format_evidence`).
- **D-06:** Remove **`QnAConfidence`** from **`GigachatRUSynthesisResult`** and all **`out_details`** keys named **`confidence`**; remove **`chat.py`** branches that copy `confidence` into `details`.
- **D-07:** **`QnAConfidence` model** may remain in `api_contracts.py` temporarily only if still referenced by legacy tests — **goal:** zero references in response path; prefer delete if grep-clean.

</decisions>

<canonical_refs>

## Canonical references

- `.planning/REQUIREMENTS.md` — AGT-03, AGT-04, AGT-05, SRCH-03, WEB-01, API-05
- `.planning/ROADMAP.md` — Phase 9 success criteria
- `src/graph/f1_turn_graph.py` — current graph (replace orchestration)
- `src/answer/gigachat_rag.py` — GigaChat JSON helpers
- `src/graph/tavily_tool.py` — Tavily wrapper
- `src/api/chat.py` — `/next_message` assembly
- `src/models/api_contracts.py` — response models

</canonical_refs>

---

*Phase: 09-supervisor-agent-graph-no-confidence-web-provenance*
