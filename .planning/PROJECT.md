# F1 Assistant (GigaChat + LangGraph)

## What This Is

Asynchronous chat assistant for Formula 1 focused on novice fans who mostly know recent seasons but want to learn the full history and context. The system combines **RAG over historical F1 data** with **web search (Tavily via LangChain)** when retrieval is insufficient, orchestrated by a **LangGraph supervisor with GigaChat at the core**, then returns structured, reliable answers in chat. Primary interaction language is Russian, with bilingual RU/EN support for source grounding and responses.

## Core Value

The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## Current Milestone: v1.2 GigaChat supervisor — RAG sufficiency → Tavily (remove F1 API)

**Goal:** Replace the **f1api.dev** live branch with **LangGraph-orchestrated** flows: **GigaChat** supervises **RAG** and, when evidence is **empty or insufficient**, uses **LangChain + Tavily Search** (LLM-authored query → results → synthesis). Ship **operator documentation** (`README`) for setup, run, and **all `.env` keys with acquisition links**, plus **tests that validate GigaChat and configured API keys** (smoke/integration pattern).

**Target features:**

- **Supervisor graph:** LangGraph with **GigaChat**-centric routing; **RAG node** + **tool node** (Tavily); parallel fan-out where beneficial.
- **Sufficiency:** Explicit evaluation after retrieval (scores and/or LLM judge) before spending Tavily budget.
- **Tavily path:** No dedicated F1 REST client in the answer pipeline; web results feed structured RU answers with **attributed URLs**.
- **Docs & quality:** Full **README** (deploy locally, run API + Streamlit, `.env` catalog); **pytest** coverage for **live key smoke** (opt-in marker) and GigaChat ping.

**Key context:** v1.1 delivered GigaChat RAG + Streamlit + local runbook; v1.2 is an **architecture shift** for freshness and gaps while keeping async session contracts and Russian structured responses.

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

### Active (v1.2)

- **README:** setup, run, **`.env` variables** and where to obtain keys (GigaChat, Tavily, etc.).
- **Tests:** smoke/integration checks that **GigaChat** and **required `.env` keys** work when enabled.
- **WEB-01** structured **`details.web`** and Streamlit web panels (Phase 9).

### Out of Scope

- Voice mode — not required for first release.
- Advanced personalization — defer until core QA reliability is proven.

## Context

The target architecture is a **LangGraph** supervisor with delegated nodes (**RAG**, **tool/Tavily**, **synthesis**). Backend is FastAPI with async endpoints and Pydantic models for structured JSON validation. Frontend is Streamlit chat. Historical data comes from f1db loaded into ChromaDB for retrieval. When RAG context is insufficient, **Tavily web search** (via LangChain) supplies external evidence instead of a dedicated Formula 1 REST API.

## Constraints

- **Accuracy**: At least 98% correct answers on agreed validation set — primary success metric.
- **Latency**: Typical response time up to 10 seconds for standard non-heavy requests.
- **Language**: Russian user interaction with Russian+English handling for data grounding.
- **Auth**: Access controlled via per-user code allowlist.
- **Deployment (v1.2):** Local run — API + Streamlit; Docker not a milestone goal unless scoped later.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG-first, web-second response policy (v1.2) | Stabilize quality; Tavily only when RAG insufficient | Replace f1api live branch with LangGraph gate + Tavily tool. |
| Explicit degraded-mode when web search fails | Prevent silent failures | Reuse pattern from Phase 05; message/RU copy updated for Tavily timeouts. |
| Per-user code allowlist authentication for v1 | Lightweight access control with minimal implementation overhead | Delivered Phase 01; unchanged. |
| RU-first UX with RU/EN support | Users are Russian-speaking while source data is primarily English | — Pending |
| v1.1: GigaChat classic RAG + template fallback | LLM reads retrieved chunks; outages must not fabricate silently | Primary synthesis in `gigachat_rag.py` (replaces `russian_qna.py`); template path on GigaChat outage. |
| v1.1: No Docker | User—v1.1 delivery | Shipped RUN-01. |
| v1.2: Tavily + LangGraph supervisor | User request; remove F1 REST dependency | GigaChat core; LangChain Tavily tool; README + env tests. |

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
*Last updated: 2026-03-28 — Phase 8 complete (LangGraph + Tavily; f1api removed from `/next_message`)*
