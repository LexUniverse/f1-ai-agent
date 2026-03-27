# F1 Assistant (GigaChat + LangGraph)

## What This Is

Asynchronous chat assistant for Formula 1 focused on novice fans who mostly know recent seasons but want to learn the full history and context. The system combines RAG over historical F1 data with live API lookups when needed, then returns structured, reliable answers in chat. Primary interaction language is Russian, with bilingual RU/EN support for source grounding and responses.

## Core Value

The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## Current Milestone: v1.1 Product surface & GigaChat RAG

**Goal:** Layer **GigaChat-backed classic RAG** on the existing retrieval stack and ship a **Streamlit** chat UI, using **local run only** (no Docker for this milestone).

**Target features:**

- **Phase 6 (priority):** Retrieval (Phase 3 pipeline) → prompt with chunks → **GigaChat** generation → Russian answer; implement **`src/answer/gigachat_rag.py`** in place of **`russian_qna.py`** as the primary synthesis path; **template / deterministic fallback** when GigaChat is unavailable.
- **Phase 7:** **Streamlit** UI — `access_code` + question → `/start_chat` → `session_id` → poll `/message_status` → `/next_message`; display **message**, **confidence**, **citations**, and **`details.live`** when present.
- **Runbook:** Local dev documented as **`python api.py`** (or equivalent documented entry) **+ Streamlit** app; **no Docker** for v1.1.

**Key context:** v1.0 validated API contracts, RAG, structured details, and live enrichment; v1.1 adds the LLM synthesis path and operator-facing UI without changing the async session model.

## Requirements

### Validated

- ✓ Access is restricted by per-user code allowlist authentication — validated in Phase 01 (access-control)
- ✓ Async API contracts are typed and deterministic for session bootstrap, status polling, and next-message flow — validated in Phase 02 (async-backend-contracts)
- ✓ Historical answers are grounded in indexed f1db retrieval with traceable evidence — validated in Phase 03 (historical-rag-grounding)
- ✓ Russian `/next_message` responses expose structured QnA details, explicit confidence, numbered sources, and safe abstention when evidence is missing — validated in Phase 04 (ru-q-a-answer-reliability)
- ✓ Live enrichment after historical retrieval uses a deterministic gate, surfaces `LiveDetails` / `as_of` in responses, and returns a fixed Russian degraded message when f1api.dev is unavailable — validated in Phase 05 (live-enrichment-freshness)

### Active (v1.1)

- [ ] User can ask F1 questions in Russian and receive **GigaChat-grounded** answers when retrieval returns evidence, with **template fallback** if the LLM path fails.
- [ ] User can run the stack **locally** via documented **API + Streamlit** commands (no Docker in v1.1).

### Out of Scope

- Voice mode — not required for first release.
- Advanced personalization — defer until core QA reliability is proven.

## Context

The target architecture is a multi-agent graph on LangGraph with a supervisor and delegated nodes (planner, rag, llm, tool_call, evaluator). Backend is FastAPI with async endpoints and Pydantic models for structured JSON validation. Frontend is Streamlit chat. Historical data comes from f1db loaded into ChromaDB for retrieval. Live updates come from f1api.dev and should be used conditionally when RAG context is insufficient.

## Constraints

- **Accuracy**: At least 98% correct answers on agreed validation set — primary success metric.
- **Latency**: Typical response time up to 10 seconds for standard non-heavy requests.
- **Language**: Russian user interaction with Russian+English handling for data grounding.
- **Auth**: Access controlled via per-user code allowlist.
- **Deployment (v1.1):** Local run only — API + Streamlit; Docker explicitly out of scope for this milestone.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG-first, API-second response policy | Reduces external dependency and stabilizes response quality | Enforced in `/next_message` after Phase 05 (retrieve → evidence → live branch only when empty + gate). |
| Explicit degraded-mode message when live API fails | Prevent silent failures and overconfident hallucinations | `LIVE_UNAVAILABLE` + `LIVE_UNAVAILABLE_MESSAGE_RU` from Phase 05. |
| Per-user code allowlist authentication for v1 | Lightweight access control with minimal implementation overhead | Delivered Phase 01; unchanged. |
| RU-first UX with RU/EN support | Users are Russian-speaking while source data is primarily English | — Pending |
| v1.1: GigaChat classic RAG + template fallback | LLM reads retrieved chunks; outages must not fabricate silently | Primary synthesis in `gigachat_rag.py` (replaces `russian_qna.py`); template path on GigaChat outage. |
| v1.1: No Docker | User preference for v1.1 delivery | Local `python api.py` + Streamlit only; document in RUN-01. |

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
*Last updated: 2026-03-27 — milestone v1.1 scoped (GigaChat RAG + Streamlit, local run)*
