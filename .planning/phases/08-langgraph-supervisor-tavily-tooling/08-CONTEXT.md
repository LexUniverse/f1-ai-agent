# Phase 8: LangGraph Supervisor & Tavily Tooling - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Each user turn runs through a **compiled LangGraph** (GigaChat-centric) with explicit nodes for **retrieval-backed RAG**, a **RAG sufficiency gate**, optional **LangChain Tavily** tool use only when the gate fails, and **unified synthesis** into the existing **structured Russian** API contract. **f1api.dev** (and all **`/next_message`** branches that call it) **must be removed** per **SRCH-02**. Tool usage is **bounded** (caps, timeouts); Tavily/tool failures surface as **explicit failed responses** with a **dedicated machine-readable code** and **fixed Russian** user-visible copy (Phase 5-style hygiene, **not** reusing `LIVE_UNAVAILABLE`).

**Phase 8 does not** deliver full **WEB-01** `details.web` schema or Streamlit web panels — that is **Phase 9**. **Phase 8** must still satisfy **SRCH-01** by surfacing **URLs in citations** (`sources_block_ru` / citation list).

</domain>

<decisions>
## Implementation Decisions

### RAG sufficiency gate (AGT-02)
- **D-01:** **Hybrid gate:** Use **fast deterministic rules** for obvious cases (e.g. **empty evidence** → insufficient; clear pass cases as defined in code + tests). Use a **GigaChat sufficiency judge** only on **borderline** retrieval outcomes — not after every retrieval.
- **D-02:** **Borderline definition:** Driven by **retriever score band** — when hits exist but **top score** falls in a **documented band** (anchored to current `min_score` / `top_k` behavior in `retrieve_historical_context`), invoke the judge. Exact numeric thresholds are **Claude’s discretion** but must be **locked in code + pytest**.

### Tavily budget & degraded mode
- **D-03:** **At most one Tavily invocation per user turn** (single GigaChat-authored query). No second-hop reformulation in Phase 8 unless explicitly replanned later.
- **D-04:** On Tavily/tool transport failure, timeout, or empty unusable results after the single allowed call: **`status: "failed"`**, **`details["code"] == "WEB_SEARCH_UNAVAILABLE"`**, **`evidence": []`**, omit `structured_answer` / `confidence` on that branch where consistent with existing abstention hygiene, and a **single fixed Russian `message`** string (pytest-stable). **Do not** reuse **`LIVE_UNAVAILABLE`** — that code is tied to the **removed f1api** path; a **new** code avoids misleading operators and clients.

### Web provenance (Phase 8 vs Phase 9)
- **D-05:** **Citations path only in Phase 8:** Ensure **URLs** appear in **`structured_answer.sources_block_ru`** (and citation numbering) when Tavily contributed. **Defer** structured **`details.web`** (WEB-01 shape) to **Phase 9** unless implementation reveals a trivial additive stub — default is **no** new `details.web` in Phase 8.

### f1api removal (SRCH-02)
- **D-06:** **Remove f1api from the answer pipeline entirely:** no `f1_api_client` usage from **`/next_message`**, remove **live / f1api synthesis** branches in `src/api/chat.py` (and related **`gigachat_synthesize_*`** entry points used only for f1api context). **Delete or stub** `src/integrations/f1api_client.py` and **strip dependencies** that exist only for that path; **update tests** to mock Tavily/LangGraph paths instead. **Do not** keep a **feature flag** that re-enables f1api for normal operation.

### LangGraph topology & FastAPI execution (AGT-01)
- **D-07:** **Explicit supervisor-style graph:** named nodes matching the roadmap — e.g. **resolve/retrieve → format evidence → sufficiency → (optional) Tavily tool → synthesize** — with clear edges for RAG vs tool branching (not an opaque inline script).
- **D-08:** Invoke the **sync** LangGraph runner via **`asyncio.to_thread`** (or equivalent thread-pool offload) from the FastAPI route so the event loop is not blocked by LLM/graph work; document the contract in plan/research notes.

### Claude's Discretion
- Exact **LangGraph state schema**, node naming, and **langgraph/langchain** package pins consistent with `requirements.txt`.
- Exact **judge prompt** shape and **score band** constants (within D-02).
- **Russian** fixed string for `WEB_SEARCH_UNAVAILABLE` (must remain **pytest-stable** once chosen).
- Whether to merge **entity resolution** inside the graph vs keep the current `resolve_entities` pre-step before `invoke` (prefer minimal change to session contract).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 8 goal, success criteria, AGT-01, AGT-02, SRCH-01, SRCH-02
- `.planning/REQUIREMENTS.md` — **AGT-01**, **AGT-02**, **SRCH-01**, **SRCH-02**
- `.planning/PROJECT.md` — v1.2 supervisor, Tavily, f1api removal, degraded-mode principle

### Prior phase context (contracts to preserve or supersede)
- `.planning/phases/07-streamlit-ui-local-run/07-CONTEXT.md` — UI expectations until WEB-01; `details.live` primary for Streamlit today
- `.planning/phases/06-gigachat-classic-rag/06-CONTEXT.md` — `gigachat_rag.py`, template fallback, `details.synthesis`, structured answer mapping
- `.planning/phases/05-live-enrichment-freshness/05-CONTEXT.md` — **superseded** for `/next_message` enrichment; keep only **degraded-mode patterns** as *spiritual* reference, not codes tied to f1api
- `.planning/phases/02-async-backend-contracts/02-CONTEXT.md` — session lifecycle, `/next_message` contract

### Research
- `.planning/research/ARCHITECTURE.md` — graph nodes, f1api removal targets, thread offload note
- `.planning/research/PITFALLS.md` — Tavily hallucination caps, event-loop blocking
- `.planning/research/SUMMARY.md` — stack direction (LangGraph + LangChain Tavily)

### Implementation anchors
- `src/api/chat.py` — current `/next_message` orchestration; integration point for LangGraph runner
- `src/answer/gigachat_rag.py` — synthesis functions; may split or add “RAG + web evidence” prompt path
- `src/models/api_contracts.py` — `NextMessageResponse`, `StructuredRUAnswer`, `QnAConfidence`
- `src/retrieval/` — retrieval and `format_evidence` (RAG node inputs)
- `src/integrations/f1api_client.py` — **removal target** per D-06

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`src/api/chat.py`**: session + `resolve_entities` → `retrieve_historical_context` → `format_evidence` → branching; replace f1api/live branches with **graph invoke** result mapping into `details`.
- **`src/answer/gigachat_rag.py`**: `gigachat_synthesize_historical` and related routes; extend or factor for **web-grounded** synthesis when Tavily results exist.
- **`src/models/api_contracts.py`**: existing success/failure envelopes — align `WEB_SEARCH_UNAVAILABLE` with established `failed` payload hygiene.
- **`src/live/gate.py`**: **`requires_live_data`** may inform sufficiency / “freshness intent” **without** calling f1api — evaluate reuse vs rename in planning.

### Established Patterns
- **Template fallback** + **`details.synthesis.route`** + disclosure on GigaChat outage (Phase 6) must remain where applicable on **non-failed** paths.
- **Phase 4/5**: `RETRIEVAL_NO_EVIDENCE` vs **failed** codes — new **`WEB_SEARCH_UNAVAILABLE`** is a **failed** outcome, distinct from abstention codes.

### Integration Points
- **FastAPI `request.app.state`**: today may expose `f1_api_client` — remove; inject **Tavily / LangChain** config or clients as needed for the tool node.
- **Tests** under `tests/`: replace f1api mocks with graph + Tavily mocks; keep default CI **offline**.

</code_context>

<specifics>
## Specific Ideas

User question during Q4: why discuss **f1api** when it is being removed — **because Phase 5 degraded-mode was the closest prior art** for timeouts/outages; the **chosen** failure code **`WEB_SEARCH_UNAVAILABLE`** deliberately **does not** reuse **`LIVE_UNAVAILABLE`** (f1api-specific). User locked **Q1:B, Q2:A, Q3:A, Q4:A, Q5:A, Q6:A, Q7:A, Q8:A** on 2026-03-28.

</specifics>

<deferred>
## Deferred Ideas

- **Structured `details.web` + Streamlit web panels** — **Phase 9 (WEB-01)**.
- **Second Tavily hop / query reformulation loop** — out of scope for Phase 8 per D-03; backlog if needed later.
- **README / credential smokes** — **Phase 10 (DOC-01, TST-01)**.

### Reviewed Todos (not folded)
- None (`todo match-phase` returned no items for phase 8).

</deferred>

---

*Phase: 08-langgraph-supervisor-tavily-tooling*
*Context gathered: 2026-03-28*
