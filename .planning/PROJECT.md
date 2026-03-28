# F1 Assistant (GigaChat + LangGraph)

## What This Is

Asynchronous chat assistant for Formula 1 focused on novice fans who mostly know recent seasons but want to learn the full history and context. The system combines **RAG over historical F1 data** with **web search (Tavily via LangChain)** when needed, orchestrated by a **LangGraph + LangChain** turn: a **supervisor** (GigaChat) **accepts or rejects candidate answers** from a **worker agent** that first answers **from RAG only**, then uses the **search tool** only when the supervisor demands a better answer. Primary interaction language is Russian, with bilingual RU/EN support for source grounding and responses.

## Core Value

The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## Current Milestone: v1.3 — Supervisor–agent graph, no confidence, UX & docs

**Goal:** Replace the **linear** Phase-8 graph (retrieve → sufficiency → Tavily → synthesize) with an explicit **supervisor / Agent 1** loop built with **LangGraph + LangChain**: Agent 1 first produces an answer **using only RAG**; the **supervisor** judges whether it adequately answers the **user’s original question**; if not, the supervisor instructs Agent 1 to call the **web search tool**, integrate results, and submit a **new** answer; the supervisor judges again. **At most two** search-backed iterations after the initial RAG attempt; if the answer is still inadequate, return a **fixed Russian message** that the system could not find a satisfactory answer. **Remove `confidence` from the product entirely** (schemas, `details`, Streamlit, tests) — not merely hidden in UI. Also: **`details.web`** when search is used, **Streamlit** chronological chat with **message first** and **expandable sources**, **README** + **opt-in credential smokes**.

**Target features:**

- **Architecture:** LangGraph state machine + LangChain tool binding for **Tavily**; **supervisor** node evaluates **answer vs user question**; **Agent 1** node generates from **RAG-only** context until supervisor routes to **tool use**, then re-generates with **RAG + web** snippets.
- **Search cap:** After the **first RAG answer**, supervisor may trigger **up to two** search-and-rewrite cycles; then **terminal “не удалось найти ответ”** (or agreed copy) if still insufficient.
- **API:** No **`confidence`** fields anywhere; structured **`details.web`** when the tool contributed; citations/sources remain.
- **Streamlit:** Append-order history; primary **`message`**; sources in **expander**; no confidence (aligned with API).
- **Docs & quality:** **README** / **`.env.example`**; **pytest** smokes (marker/opt-in).

**Key context:** Phase 8 shipped a simpler gate. Operator testing showed weak **web synthesis** and meaningless **flat confidence**. v1.3 makes **quality gating explicit** via the supervisor and drops confidence as a signal.

## Requirements

### Validated

- ✓ Access is restricted by per-user code allowlist authentication — validated in Phase 01 (access-control)
- ✓ Async API contracts are typed and deterministic for session bootstrap, status polling, and next-message flow — validated in Phase 02 (async-backend-contracts)
- ✓ Historical answers are grounded in indexed f1db retrieval with traceable evidence — validated in Phase 03 (historical-rag-grounding)
- ✓ Russian `/next_message` responses expose structured QnA details, numbered sources, and safe abstention when evidence is missing — validated in Phase 04 (ru-q-a-answer-reliability); *Phase 4 also shipped explicit confidence — **superseded by v1.3 (confidence removed)**.*
- ✓ Live enrichment after historical retrieval uses a deterministic gate, surfaces `LiveDetails` / `as_of` in responses, and returns a fixed Russian degraded message when f1api.dev is unavailable — validated in Phase 05 (live-enrichment-freshness)
- ✓ GigaChat classic RAG on historical paths with hybrid citations and explicit template fallback + disclosure when the LLM fails — validated in Phase 06 (gigachat-classic-rag); *confidence on that path superseded by v1.3.*
- ✓ Streamlit operator UI (`/start_chat`, status polling, `/next_message`) with citations and synthesis metadata; documented local **API + Streamlit** run — validated in Phase 07 (streamlit-ui-local-run); *UI confidence superseded by v1.3.*
- ✓ **LangGraph** turn with **RAG** + **Tavily (LangChain)** and **GigaChat**; **f1api.dev** removed from answer path — validated in Phase 08 (langgraph-supervisor-tavily-tooling); *linear orchestration superseded by v1.3 supervisor–agent loop.*
- ✓ **Supervisor–Agent 1** LangGraph (RAG-first, ≤2 Tavily rounds, AGT-05 terminal copy), **no `confidence`** in synthesis types or graph outputs, **`details.web`** when search used — validated in Phase 09 (supervisor-agent-graph-no-confidence-web-provenance).

### Active (v1.3)

- **UI-04, UI-05:** Chronological chat; message first; expandable sources.
- **DOC-01, TST-01:** README + `.env` catalog; opt-in live smokes.

### Out of Scope

- Voice mode — not required for first release.
- Advanced personalization — defer until core QA reliability is proven.
- **Confidence as a product field** — removed in v1.3; not deferred for recalibration.

## Context

Backend is FastAPI with async endpoints and Pydantic models. Frontend is Streamlit. Historical data: f1db in ChromaDB. Web: **Tavily** via **LangChain** tools inside a **LangGraph** compiled graph; **GigaChat** drives supervisor and worker prompts. The v1.3 graph is the **source of truth** for when search runs (supervisor decision after seeing Agent 1’s RAG-only answer), not only a pre-synthesis retrieval score.

## Constraints

- **Accuracy**: At least 98% correct answers on agreed validation set — primary success metric.
- **Latency**: Typical response time up to 10 seconds for standard non-heavy requests (supervisor loops may tighten budgets per plan).
- **Language**: Russian user interaction with Russian+English handling for data grounding.
- **Auth**: Access controlled via per-user code allowlist.
- **Deployment:** Local run — API + Streamlit; Docker not a milestone goal unless scoped later.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG-first, web-second response policy (v1.2) | Stabilize quality | v1.3 keeps RAG-first **via Agent 1**; web only after **supervisor** rejection. |
| Explicit degraded-mode when web search fails | Prevent silent failures | Preserve; align copy with new terminal failure path where relevant. |
| v1.3: Supervisor judges answers | Linear sufficiency gate insufficient for answer quality | Supervisor accepts/rejects **full candidate answers** vs user question. |
| v1.3: Max two search iterations | Cost/latency + avoid infinite loops | After 2 tool cycles post–RAG attempt, fixed RU “could not find answer”. |
| v1.3: Remove confidence entirely | Misleading constant / no calibration | Drop from schemas, details, Streamlit, tests. |

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
*Last updated: 2026-03-28 — Phase 9 complete: supervisor graph, API-05, WEB-01; next Streamlit UX (Phase 10).*
