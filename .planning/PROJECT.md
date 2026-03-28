# F1 Assistant (GigaChat + LangGraph)

## What This Is

Asynchronous chat assistant for Formula 1 focused on novice fans who mostly know recent seasons but want to learn the full history and context. The system combines **RAG over historical F1 data** with **web search (Tavily via LangChain)** when retrieval is insufficient, orchestrated by a **LangGraph supervisor with GigaChat at the core**, then returns structured, reliable answers in chat. Primary interaction language is Russian, with bilingual RU/EN support for source grounding and responses.

## Core Value

The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## Current Milestone: v1.3 — Web answer fidelity & Streamlit UX

**Goal:** Fix the **Tavily branch** so the user sees a **direct Russian answer to their original question**, synthesized from search snippets (not an echo of the search query or link-only noise). Align **Streamlit** with operator expectations: **chronological chat** (newest turns next to the composer), **message text first** with **sources in a collapsible block**, and **no confidence UI** until scores are meaningful. Ship **structured web provenance** in the API, plus **README / `.env` catalog** and **opt-in credential smokes** carried forward from v1.2.

**Target features:**

- **Answer pipeline:** Unchanged order at a high level — **RAG first**; **Tavily only** when RAG is judged insufficient; then **synthesis must use snippets to answer the user’s question** (prompts, validation, and tests for regressions like «кто победил в сезоне 2021»).
- **API contract:** **`details.web`** (query, URLs, snippets/metadata) when search contributed; Streamlit consumes it for display logic.
- **Streamlit:** Append turns in **time order**; default view = **assistant `message` only**; **источники** in **`st.expander`**; **remove** уверенность from the UI.
- **Docs & quality:** **README** + **`.env.example`** completeness; **pytest** smokes for live keys (marker/opt-in), default CI offline.

**Key context:** v1.2 Phase 8 shipped LangGraph + Tavily and removed f1api from the answer path. Manual testing showed **`gigachat_web`** sometimes returning non-answers (question echo / search-oriented text). Streamlit currently **`insert(0, …)`** messages, so **new replies appear at the top**; confidence is a **constant middle tier** in the web path — misleading in UI.

## Requirements

### Validated

- ✓ Access is restricted by per-user code allowlist authentication — validated in Phase 01 (access-control)
- ✓ Async API contracts are typed and deterministic for session bootstrap, status polling, and next-message flow — validated in Phase 02 (async-backend-contracts)
- ✓ Historical answers are grounded in indexed f1db retrieval with traceable evidence — validated in Phase 03 (historical-rag-grounding)
- ✓ Russian `/next_message` responses expose structured QnA details, explicit confidence, numbered sources, and safe abstention when evidence is missing — validated in Phase 04 (ru-q-a-answer-reliability)
- ✓ Live enrichment after historical retrieval uses a deterministic gate, surfaces `LiveDetails` / `as_of` in responses, and returns a fixed Russian degraded message when f1api.dev is unavailable — validated in Phase 05 (live-enrichment-freshness)
- ✓ GigaChat classic RAG on historical and live success paths with hybrid citations, deterministic confidence, and explicit template fallback + disclosure when the LLM fails — validated in Phase 06 (gigachat-classic-rag)
- ✓ Streamlit operator UI (`/start_chat` with question, status polling, `/next_message`) showing message, confidence, citations, live and synthesis metadata; documented local **API + Streamlit** run (`python api.py`, `streamlit run streamlit_app.py`) without Docker — validated in Phase 07 (streamlit-ui-local-run)
- ✓ **LangGraph** turn orchestration (**RAG** + **Tavily** via LangChain), **GigaChat** sufficiency judge and synthesis, **`asyncio.to_thread`** from async `/next_message`; **f1api.dev** removed from answer path; **`WEB_SEARCH_UNAVAILABLE`** fixed Russian copy — validated in Phase 08 (langgraph-supervisor-tavily-tooling)

### Active (v1.3)

- **SRCH-03 / synthesis:** Tavily path answers the **original user question** in Russian using returned page content; no query-echo or sources-only as the primary reply.
- **WEB-01:** Structured **`details.web`** when search is used; clients can show provenance separately from RAG citations.
- **UI-04 — UI-06:** Streamlit chronological layout; primary text + expandable sources; confidence hidden in UI.
- **DOC-01 / TST-01:** README + `.env` acquisition links; opt-in live smokes.

### Out of Scope

- Voice mode — not required for first release.
- Advanced personalization — defer until core QA reliability is proven.
- **Recalibrated confidence scores** for the web path — deferred; UI hides confidence until a meaningful signal exists.

## Context

The target architecture is a **LangGraph** supervisor with delegated nodes (**RAG**, **tool/Tavily**, **synthesis**). Backend is FastAPI with async endpoints and Pydantic models for structured JSON validation. Frontend is Streamlit chat. Historical data comes from f1db loaded into ChromaDB for retrieval. When RAG context is insufficient, **Tavily web search** (via LangChain) supplies external evidence instead of a dedicated Formula 1 REST API.

## Constraints

- **Accuracy**: At least 98% correct answers on agreed validation set — primary success metric.
- **Latency**: Typical response time up to 10 seconds for standard non-heavy requests.
- **Language**: Russian user interaction with Russian+English handling for data grounding.
- **Auth**: Access controlled via per-user code allowlist.
- **Deployment:** Local run — API + Streamlit; Docker not a milestone goal unless scoped later.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG-first, web-second response policy (v1.2) | Stabilize quality; Tavily only when RAG insufficient | Replace f1api live branch with LangGraph gate + Tavily tool. |
| Explicit degraded-mode when web search fails | Prevent silent failures | Reuse pattern from Phase 05; message/RU copy updated for Tavily timeouts. |
| Per-user code allowlist authentication for v1 | Lightweight access control with minimal implementation overhead | Delivered Phase 01; unchanged. |
| RU-first UX with RU/EN support | Users are Russian-speaking while source data is primarily English | — |
| v1.3: Web synthesis must answer the user’s question | Operator testing showed bad `gigachat_web` outputs | Tighten prompts / post-checks + regression tests. |
| v1.3: Hide confidence in Streamlit | Web path used a flat confidence; misleading | UI omits tier/score until recalibration. |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-28 — Milestone v1.3 started (web fidelity + Streamlit UX + docs/smokes)*
