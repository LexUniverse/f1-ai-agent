# Roadmap: F1 Assistant (GigaChat + LangGraph)

## Overview

This roadmap delivers a trust-first Formula 1 assistant in Russian. **v1.0–v1.2 (Phases 1–8)** shipped API, RAG, GigaChat paths, Streamlit, and a **linear** LangGraph with **RAG gate → Tavily**.

**v1.3 (Phases 9–11)** **replaces** that linear orchestration with a **supervisor + Agent 1** loop (**LangGraph + LangChain**): **RAG-only** first answer → **supervisor** accepts or rejects → on reject, **Agent 1** uses the **search tool** (up to **two** iterations) → if still unacceptable, **fixed Russian failure message**. **Confidence is removed everywhere.** Then **Streamlit** layout polish and **README / credential smokes**.

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
- [x] **Phase 8: LangGraph Supervisor & Tavily Tooling** - *(Completed: 2026-03-28; linear graph — superseded by Phase 9 design)*
- [x] **Phase 9: Supervisor–Agent Graph, No Confidence, Web Provenance** - *(Completed: 2026-03-28)* **AGT-03, AGT-04, AGT-05**, **SRCH-03**, **WEB-01**, **API-05**: LangGraph+LangChain supervisor loop (RAG first, ≤2 searches, terminal RU failure); strip all `confidence` from models and payloads; `details.web`; tests for loop bounds and answer quality.
- [ ] **Phase 10: Streamlit Chat UX** - **UI-04**, **UI-05**: chronological append-order, message-first + expandable sources (no confidence — **API-05**).
- [ ] **Phase 11: README & Credential Smokes** - **DOC-01**, **TST-01**.

## Phase Details

### Phases 1–8

**Goals and requirements** as historically delivered; Phase 8 graph is **replaced** by Phase 9 architecture (see phase docs under `.planning/phases/`).

### Phase 9: Supervisor–Agent Graph, No Confidence, Web Provenance
**Goal:** **Supervisor** evaluates **full answers** from **Agent 1**; **RAG-only** first; **LangChain Tavily tool** only after supervisor rejection; **≤2** search iterations; then **AGT-05** failure message. **Remove confidence** from API. **Structured `details.web`.**  
**Depends on:** Phase 8 codebase (refactor in place).  
**Requirements:** AGT-03, AGT-04, AGT-05, SRCH-03, WEB-01, API-05  
**Success Criteria** (what must be TRUE):
  1. A compiled **LangGraph** run per turn includes an explicit **supervisor** decision step on **candidate answer text** vs **user question** (not only retrieval score).
  2. **Agent 1**’s **first** candidate uses **no web tool**; web tool invocations are **count-limited** to **two** after that, driven by supervisor rejection.
  3. After **two** unsuccessful search-backed attempts (per AGT-04), the user receives the **AGT-05** fixed Russian message and no fabricated answer.
  4. **No** `confidence` field appears in `/next_message` JSON, Pydantic models, or documented examples.
  5. When the tool contributed to the **accepted** answer, **`details.web`** is populated; final **`message`** satisfies **SRCH-03** (answers original question).
**Plans:** TBD

### Phase 10: Streamlit Chat UX
**Goal:** Operator chat matches API: **newest near input**, **clean default**, **sources on demand**, **no confidence**.  
**Depends on:** Phase 9 (API-05 stable).  
**Requirements:** UI-04, UI-05  
**Success Criteria** (what must be TRUE):
  1. Multiple turns: latest user + assistant visible **just above** composer (**append** semantics).
  2. Assistant **body** visible without expanders; **sources** behind expander.
  3. No confidence UI elements.
**Plans:** TBD

### Phase 11: README & Credential Smokes
**Goal:** Onboarding and optional live key verification.  
**Depends on:** Phase 10  
**Requirements:** DOC-01, TST-01  
**Success Criteria:** *(unchanged — full `.env` catalog, pytest marker, offline default)*  
**Plans:** TBD

## Progress

**Execution Order:** … → 8 → **9** → **10** → **11**

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1–8 | … | Complete | 2026-03-27 — 2026-03-28 |
| 9. Supervisor–Agent Graph, No Confidence, Web Provenance | 2/2 | Complete | 2026-03-28 |
| 10. Streamlit Chat UX | 0/TBD | Planned | — |
| 11. README & Credential Smokes | 0/TBD | Planned | — |
