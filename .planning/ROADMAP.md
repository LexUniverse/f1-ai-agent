# Roadmap: F1 Assistant (GigaChat + LangGraph)

## Overview

This roadmap delivers a trust-first Formula 1 assistant in Russian by sequencing access control, API contracts, grounded retrieval, structured answer quality, and live-data reliability. Each phase maps to a coherent requirement group and defines observable outcomes that can be verified directly in the product.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Access Control** - Restrict assistant usage to valid personal allowlist codes. *(Completed: 2026-03-27)*
- [x] **Phase 2: Async Backend Contracts** - Provide stable async chat endpoints with strict schemas. *(Completed: 2026-03-27)*
- [ ] **Phase 3: Historical RAG Grounding** - Ground responses in f1db with multilingual entity matching and traceability.
- [ ] **Phase 4: RU Q&A Answer Reliability** - Produce structured Russian answers with confidence, citations, and abstention.
- [ ] **Phase 5: Live Enrichment & Freshness** - Add conditional live API enrichment with degraded-mode and freshness guarantees.

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
- [ ] 02-01-PLAN.md — Contract foundation: typed schemas, unified error envelope, and `/start_chat` bootstrap verification.
- [ ] 02-02-PLAN.md — Async lifecycle completion: session-state mapping, polling-safe status, and `/next_message` flow contract.

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
**Plans**: TBD

### Phase 5: Live Enrichment & Freshness
**Goal**: Live data augments answers only when needed, with transparent freshness and outage behavior.
**Depends on**: Phase 4
**Requirements**: LIVE-01, LIVE-02, LIVE-03
**Success Criteria** (what must be TRUE):
  1. User receives live-enriched answers when retrieval context is insufficient and current data is required.
  2. User receives an explicit degraded-mode message when live API dependency is unavailable.
  3. Live-dependent answers include freshness metadata (`as_of`) visible in the response.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 2.1 -> 2.2 -> 3 -> 3.1 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Access Control | 2/2 | Complete | 2026-03-27 |
| 2. Async Backend Contracts | 2/2 | Complete | 2026-03-27 |
| 3. Historical RAG Grounding | 0/2 | Not started | - |
| 4. RU Q&A Answer Reliability | 0/TBD | Not started | - |
| 5. Live Enrichment & Freshness | 0/TBD | Not started | - |
