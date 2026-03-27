# F1 Assistant (GigaChat + LangGraph)

## What This Is

Asynchronous chat assistant for Formula 1 focused on novice fans who mostly know recent seasons but want to learn the full history and context. The system combines RAG over historical F1 data with live API lookups when needed, then returns structured, reliable answers in chat. Primary interaction language is Russian, with bilingual RU/EN support for source grounding and responses.

## Core Value

The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## Requirements

### Validated

- ✓ Access is restricted by per-user code allowlist authentication — validated in Phase 01 (access-control)
- ✓ Async API contracts are typed and deterministic for session bootstrap, status polling, and next-message flow — validated in Phase 02 (async-backend-contracts)
- ✓ Historical answers are grounded in indexed f1db retrieval with traceable evidence — validated in Phase 03 (historical-rag-grounding)
- ✓ Russian `/next_message` responses expose structured QnA details, explicit confidence, numbered sources, and safe abstention when evidence is missing — validated in Phase 04 (ru-q-a-answer-reliability)

### Active

- [ ] User can ask F1 questions in Russian and get accurate, structured answers.
- [ ] System uses RAG first and calls live F1 API only when required information is missing.
- [ ] If live API is unavailable, system explicitly reports degraded mode and uncertainty.
- [ ] Service is deployable via Docker with working backend API and chat frontend.

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
- **Deployment**: Dockerized backend and frontend required for v1 delivery.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| RAG-first, API-second response policy | Reduces external dependency and stabilizes response quality | — Pending |
| Explicit degraded-mode message when live API fails | Prevent silent failures and overconfident hallucinations | — Pending |
| Per-user code allowlist authentication for v1 | Lightweight access control with minimal implementation overhead | — Pending |
| RU-first UX with RU/EN support | Users are Russian-speaking while source data is primarily English | — Pending |

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
*Last updated: 2026-03-27 after Phase 04 completion*
