# Roadmap: F1 Assistant (GigaChat + LangGraph)

## Overview

This roadmap delivers a trust-first Formula 1 assistant in Russian. **v1.0 (Phases 1–5)** shipped core API, RAG, RU contracts, and live enrichment. **v1.1 (Phases 6–7)** added **GigaChat classic RAG** and **Streamlit**. **v1.2 (Phases 8)** shipped the **LangGraph** supervisor, **RAG sufficiency → Tavily**, and removed **f1api** from the answer path.

**v1.3 (Phases 9–11)** fixes **web-path synthesis** so users get **answers to their original questions**, adds **`details.web`**, refreshes **Streamlit** (chronological chat, expandable sources, no confidence UI), and delivers **README + opt-in credential smokes**.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Access Control** - *(Completed: 2026-03-27)*
- [x] **Phase 2: Async Backend Contracts** - *(Completed: 2026-03-27)*
- [x] **Phase 3: Historical RAG Grounding** - *(Completed: 2026-03-27)*
- [x] **Phase 4: RU Q&A Answer Reliability** - *(Completed: 2026-03-27)*
- [x] **Phase 5: Live Enrichment & Freshness** - *(Completed: 2026-03-27)*
- [x] **Phase 6: GigaChat Classic RAG** - *(Completed: 2026-03-27)*
- [x] **Phase 7: Streamlit UI & Local Run** - *(Completed: 2026-03-27)*
- [x] **Phase 8: LangGraph Supervisor & Tavily Tooling** - *(Completed: 2026-03-28)*
- [ ] **Phase 9: Web Answer Pipeline & API Provenance** - **SRCH-03**, **WEB-01**: synthesis answers original user question; structured `details.web`; regression coverage (e.g. 2021 champion scenario).
- [ ] **Phase 10: Streamlit Chat UX** - **UI-04**, **UI-05**, **UI-06**: append-order history, message-first + expandable sources, hide confidence.
- [ ] **Phase 11: README & Credential Smokes** - **DOC-01**, **TST-01**: full `.env` catalog with acquisition links; opt-in live pytest marker.

## Phase Details

### Phase 1: Access Control
**Goal**: Only authorized users can use the assistant through personal access codes.  
**Requirements**: AUTH-01, AUTH-02  
**Success Criteria**: *(unchanged — see archived phase docs)*  
**Plans**: 2 (complete)

### Phase 2: Async Backend Contracts
**Goal**: Typed async chat endpoints.  
**Requirements**: API-01 … API-04  
**Plans**: 2 (complete)

### Phase 3: Historical RAG Grounding
**Goal**: f1db-grounded historical answers.  
**Requirements**: RAG-01 … RAG-03  
**Plans**: 4 (complete)

### Phase 4: RU Q&A Answer Reliability
**Goal**: Structured Russian answers with citations and abstention.  
**Requirements**: QNA-01 … QNA-03  
**Plans**: 2 (complete)

### Phase 5: Live Enrichment & Freshness
**Goal**: Live augmentation with degraded modes *(v1.0 f1api path; superseded for new freshness by Tavily in v1.2+)*.  
**Requirements**: LIVE-01 … LIVE-03  
**Plans**: 2 (complete)

### Phase 6: GigaChat Classic RAG
**Goal**: GigaChat chunk-grounded RAG + template fallback.  
**Requirements**: GC-01 … GC-03  
**Plans**: 2 (complete)

### Phase 7: Streamlit UI & Local Run
**Goal**: Local Streamlit + API runbook.  
**Requirements**: UI-01 … UI-03, RUN-01  
**Plans**: 2 (complete)

### Phase 8: LangGraph Supervisor & Tavily Tooling
**Goal**: GigaChat-centric graph; RAG gate; Tavily; no f1api in answer path.  
**Requirements**: AGT-01, AGT-02, SRCH-01, SRCH-02  
**Plans**: 2 (complete)

### Phase 9: Web Answer Pipeline & API Provenance
**Goal**: Operators and API clients get **correct Russian answers** when Tavily runs; **web provenance** is structured for UIs.  
**Depends on**: Phase 8  
**Requirements**: SRCH-03, WEB-01  
**Success Criteria** (what must be TRUE):
  1. For representative queries that route to Tavily (e.g. recent-season champion facts), the top-level **`message`** states the factual answer implied by the user question, in Russian, without substituting the search query text as the answer body.
  2. When Tavily contributed, **`details.web`** includes at least **query**, **source URLs**, and **snippet or title metadata** per hit (shape documented in code or OpenAPI).
  3. **RAG-only** turns remain correct; no regression in historical path wiring.
**Plans**: TBD

### Phase 10: Streamlit Chat UX
**Goal**: Chat layout matches operator mental model: **newest near input**, **clean default view**, **sources on demand**.  
**Depends on**: Phase 9 *(can parallelize API-only slices after Phase 9 contracts are stable — prefer sequential if `details.web` drives UI)*  
**Requirements**: UI-04, UI-05, UI-06  
**Success Criteria** (what must be TRUE):
  1. After multiple turns, scrolling to the bottom shows the **latest** user question and assistant reply **immediately above** the input row (append semantics).
  2. Assistant **answer text** is visible without opening expanders; **sources** require a deliberate expand action.
  3. **Confidence** tier/score is **not** shown in the Streamlit UI.
**Plans**: TBD

### Phase 11: README & Credential Smokes
**Goal**: Onboarding from README alone; optional live verification of secrets.  
**Depends on**: Phase 10  
**Requirements**: DOC-01, TST-01  
**Success Criteria** (what must be TRUE):
  1. README lists every required **`.env`** variable with **how to obtain** it (links or steps); commands for API + Streamlit + index build.
  2. `.env.example` matches documented variables (placeholders only).
  3. Pytest defines a **smoke/integration** marker; documented env flag runs real GigaChat + Tavily checks; default test run stays offline/mocked.
**Plans**: TBD

## Progress

**Execution Order:** … → 8 → **9** → **10** → **11**

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1–8 | … | Complete | 2026-03-27 — 2026-03-28 |
| 9. Web Answer Pipeline & API Provenance | 0/TBD | Planned | — |
| 10. Streamlit Chat UX | 0/TBD | Planned | — |
| 11. README & Credential Smokes | 0/TBD | Planned | — |
