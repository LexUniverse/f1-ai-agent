# Roadmap: F1 Assistant (GigaChat + LangGraph)

## Overview

**v1.0–v1.2:** API, RAG, GigaChat, linear LangGraph + Tavily. **v1.3 Phase 9:** Supervisor + Agent 1, **no confidence**, **`details.web`**.

**v1.4 (phases 12–14):** Fix **supervisor false negatives** (AGT-06), **one Tavily + optional single-page fetch** (AGT-07, SRCH-04), **unified API provenance** (WEB-02), **Streamlit** single expander + chronological chat (UI-04/05/06), **README + smokes** (DOC-01, TST-01).

> **Note:** Original **v1.3 phases 10–11** (Streamlit polish, README/smokes) are **not executed separately**; scope is **merged into v1.4** as phases **13–14** with expanded UI requirements (**UI-06**).

## Phases

- [x] **Phase 1: Access Control** - *(Completed: 2026-03-27)*
- [x] **Phase 2: Async Backend Contracts** - *(Completed: 2026-03-27)*
- [x] **Phase 3: Historical RAG Grounding** - *(Completed: 2026-03-27)*
- [x] **Phase 4: RU Q&A Answer Reliability** - *(Completed: 2026-03-27)*
- [x] **Phase 5: Live Enrichment & Freshness** - *(Completed: 2026-03-27)*
- [x] **Phase 6: GigaChat Classic RAG** - *(Completed: 2026-03-27)*
- [x] **Phase 7: Streamlit UI & Local Run** - *(Completed: 2026-03-27)*
- [x] **Phase 8: LangGraph Supervisor & Tavily Tooling** - *(Completed: 2026-03-28)*
- [x] **Phase 9: Supervisor–Agent Graph, No Confidence, Web Provenance** - *(Completed: 2026-03-28)*
- [ ] **Phase 12: Supervisor Reliability & Single-Pass Web** - **AGT-06, AGT-07, SRCH-04, WEB-02**: audit accept path; one Tavily per turn; URL ranking; title-first answer; optional one HTTP fetch; terminal AGT-05 after single pass; API shape for unified provenance.
- [ ] **Phase 13: Streamlit Unified Provenance & Chat UX** - **UI-04, UI-05, UI-06**: chronological append; message first; **one** collapsed provenance (RAG + web + synthesis); no duplicate sources blocks.
- [ ] **Phase 14: README & Credential Smokes** - **DOC-01, TST-01**.

## Phase Details (v1.4)

### Phase 12: Supervisor Reliability & Single-Pass Web
**Goal:** Stop spurious AGT-05; **GigaChat-only** acceptance judgment; **one** search iteration with **smarter** use of results.  
**Depends on:** Phase 9 codebase.  
**Requirements:** AGT-06, AGT-07, SRCH-04, WEB-02  
**Success criteria:**
1. Documented audit: **no** numeric accept gate on supervisor path; parse-fail / API-fail behavior explicit.
2. Graph invokes **Tavily at most once** per turn after RAG rejection; **no** second Tavily loop.
3. Worker **ranks** results, can answer from **titles/snippets**, else **fetches one** URL (bounded) before resubmitting to supervisor.
4. **`details`** (or documented extension) supports **one** UI-facing provenance payload (RAG + web + optional fetch meta).

### Phase 13: Streamlit Unified Provenance & Chat UX
**Goal:** Operator sees **one** clear expandable «происхождение» with RAG + web; main answer unduplicated.  
**Depends on:** Phase 12 (payload shape stable).  
**Requirements:** UI-04, UI-05, UI-06  
**Success criteria:**
1. Newest turn adjacent to composer; history append order.
2. No stacked redundant «Источники» + raw `web` JSON for the same facts without hierarchy.
3. Labels in **Russian** describe what each subsection is for.

### Phase 14: README & Credential Smokes
**Goal:** Onboarding + opt-in live checks.  
**Depends on:** Phase 13  
**Requirements:** DOC-01, TST-01  
**Success criteria:** Full env catalog; pytest marker; offline default CI.

## Progress

**Execution order:** … → 9 → **12** → **13** → **14**

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1–9 | … | Complete | 2026-03-27 — 2026-03-28 |
| 12. Supervisor reliability & single-pass web | 0/TBD | Planned | — |
| 13. Streamlit unified provenance & chat UX | 0/TBD | Planned | — |
| 14. README & credential smokes | 0/TBD | Planned | — |
