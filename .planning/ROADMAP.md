# Roadmap: F1 Assistant (GigaChat + LangGraph)

## Overview

This roadmap delivers a trust-first Formula 1 assistant in Russian. **v1.0 (Phases 1–5)** shipped: access control, API contracts, grounded retrieval, structured answer quality, and live-data reliability. **v1.1 (Phases 6–7)** adds **GigaChat classic RAG** (chunk-grounded generation + template fallback) and a **Streamlit** UI with **local run only** (no Docker).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Access Control** - Restrict assistant usage to valid personal allowlist codes. *(Completed: 2026-03-27)*
- [x] **Phase 2: Async Backend Contracts** - Provide stable async chat endpoints with strict schemas. *(Completed: 2026-03-27)*
- [x] **Phase 3: Historical RAG Grounding** - Ground responses in f1db with multilingual entity matching and traceability. *(Completed: 2026-03-27)*
- [x] **Phase 4: RU Q&A Answer Reliability** - Produce structured Russian answers with confidence, citations, and abstention. *(Completed: 2026-03-27)*
- [x] **Phase 5: Live Enrichment & Freshness** - Add conditional live API enrichment with degraded-mode and freshness guarantees. *(Completed: 2026-03-27)*
- [ ] **Phase 6: GigaChat Classic RAG** - Chunk-grounded Russian answers via GigaChat; `gigachat_rag.py` replaces `russian_qna.py`; template fallback on LLM outage.
- [ ] **Phase 7: Streamlit UI & Local Run** - Chat UI (`/start_chat`, status polling, `/next_message`); show message, confidence, citations, `details.live`; document `python api.py` + Streamlit (no Docker).

## Phase Details

### Phase 1: Access Control
**Goal**: Only authorized users can use the assistant through personal access codes.
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02
**Success Criteria** (what must be TRUE):
  1. User with a valid personal code can authenticate and access assistant functionality.
  2. User with an invalid or missing code is denied access with an explicit unauthorized message.
  3. Unauthorized requests are blocked before downstream chat processing runs.
**Plans**: 2 (01-01, 01-02)

### Phase 2: Async Backend Contracts
**Goal**: Clients can reliably interact with the assistant using typed asynchronous API flows.
**Depends on**: Phase 1
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. Client can start a chat session via the async start endpoint and receive a valid session handle.
  2. Client can poll message processing state via the status endpoint and receive structured status output.
  3. Client can fetch the next assistant response via the next-message endpoint in the expected async flow.
  4. Invalid request payloads are rejected with explicit schema validation errors.
**Plans**: 2 plans
Plans:
- [x] 02-01-PLAN.md — Contract foundation: typed schemas, unified error envelope, and `/start_chat` bootstrap verification.
- [x] 02-02-PLAN.md — Async lifecycle completion: session-state mapping, polling-safe status, and `/next_message` flow contract.

### Phase 3: Historical RAG Grounding
**Goal**: Historical F1 questions are answered from traceable retrieval over indexed f1db data.
**Depends on**: Phase 2
**Requirements**: RAG-01, RAG-02, RAG-03
**Success Criteria** (what must be TRUE):
  1. User receives historical F1 answers grounded in indexed f1db content from ChromaDB.
  2. User can ask using RU or EN names and aliases for drivers, teams, and races and still get relevant retrieval.
  3. User receives traceable retrieved context references that are clearly tied to final answer synthesis.
**Plans**: 4 plans
Plans:
- [x] 03-01-PLAN.md — Retrieval foundation: dictionary-first RU/EN alias resolver, deterministic Chroma retrieval, and typed evidence contracts.
- [x] 03-02-PLAN.md — Inline `/next_message` grounding flow with evidence-to-answer linkage and RAG traceability tests.
- [x] 03-03-PLAN.md — Gap closure: deterministic `f1db-csv` ingestion/indexing into Chroma with document schema and idempotent upsert tests.
- [x] 03-04-PLAN.md — Gap closure: replace simulated retriever path with real indexed-chunk query and non-mocked endpoint grounding verification.

### Phase 4: RU Q&A Answer Reliability
**Goal**: Users get structured Russian answers with explicit confidence and safe abstention when evidence is insufficient.
**Depends on**: Phase 3
**Requirements**: QNA-01, QNA-02, QNA-03
**Success Criteria** (what must be TRUE):
  1. User can ask in Russian and receive a structured answer format consistently.
  2. User answer always includes an explicit confidence level and source citations.
  3. User receives a clear abstention/degraded response instead of fabricated claims when supporting evidence is insufficient.
**Plans**: 2 plans
Plans:
- [x] 04-01-PLAN.md — Typed RU QnA models, deterministic builder (`src/answer/russian_qna.py`), `/next_message` success `details` + confidence in `message`.
- [x] 04-02-PLAN.md — Pytest contract coverage for structured answers, citations order, and `RETRIEVAL_NO_EVIDENCE` abstention.

### Phase 5: Live Enrichment & Freshness
**Goal**: Live data augments answers only when needed, with transparent freshness and outage behavior.
**Depends on**: Phase 4
**Requirements**: LIVE-01, LIVE-02, LIVE-03
**Success Criteria** (what must be TRUE):
  1. User receives live-enriched answers when retrieval context is insufficient and current data is required.
  2. User receives an explicit degraded-mode message when live API dependency is unavailable.
  3. Live-dependent answers include freshness metadata (`as_of`) visible in the response.
**Plans**: 2 plans
Plans:
- [x] 05-01-PLAN.md — Live contracts, f1api.dev client (timeout, retries, breaker), deterministic live gate, unit tests.
- [x] 05-02-PLAN.md — `/next_message` live branches, app state injection, RU freshness + LIVE_UNAVAILABLE, integration tests.

### Phase 6: GigaChat Classic RAG
**Goal**: Russian answers are produced by **GigaChat** from prompts that include **retrieved chunks**, with **deterministic template fallback** when the LLM path fails.
**Depends on**: Phase 5  
**Requirements**: GC-01, GC-02, GC-03  
**Success Criteria** (what must be TRUE):
  1. With evidence, the model response is driven by GigaChat using chunk context from the existing retrieval pipeline.
  2. GigaChat outage or error triggers a documented fallback path (template / legacy builder behavior) without silent hallucination.
  3. Primary synthesis module is `gigachat_rag.py`; `russian_qna.py` is no longer the main path (removed or helper-only).
**Plans**: (to plan) — use `/gsd-plan-phase 6`

### Phase 7: Streamlit UI & Local Run
**Goal**: Operators run **API + Streamlit locally** and use the async chat contract end-to-end with full visibility into structured fields.
**Depends on**: Phase 6  
**Requirements**: UI-01, UI-02, UI-03, RUN-01  
**Success Criteria** (what must be TRUE):
  1. User enters access code and question; app obtains and stores `session_id` from `/start_chat`.
  2. App polls `/message_status` and then `/next_message` per the async lifecycle.
  3. UI shows `message`, confidence, citations, and `details.live` when returned.
  4. README (or equivalent) documents local run: `python api.py` and Streamlit — **no Docker** for v1.1.
**Plans**: (to plan) — use `/gsd-plan-phase 7`

## Progress

**Execution Order:**
Phases execute in numeric order: … → 5 → **6** → **7**

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Access Control | 2/2 | Complete | 2026-03-27 |
| 2. Async Backend Contracts | 2/2 | Complete | 2026-03-27 |
| 3. Historical RAG Grounding | 4/4 | Complete | 2026-03-27 |
| 4. RU Q&A Answer Reliability | 2/2 | Complete | 2026-03-27 |
| 5. Live Enrichment & Freshness | 2/2 | Complete | 2026-03-27 |
| 6. GigaChat Classic RAG | 0/? | Not started | - |
| 7. Streamlit UI & Local Run | 0/? | Not started | - |
