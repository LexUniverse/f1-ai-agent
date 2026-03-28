# Requirements: F1 Assistant (GigaChat + LangGraph)

**Defined:** 2026-03-26 / **v1.3 scoped:** 2026-03-28 (revised)  
**Core Value:** The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## v1.3 Requirements (milestone active)

Scoped 2026-03-28 — **LangGraph + LangChain supervisor–worker loop** (RAG-only first answer; supervisor may direct **Agent 1** to use **Tavily tool** up to **two** times; terminal failure message if still inadequate). **Remove `confidence` from the entire product** (API + UI + models). **Web provenance** (`details.web`), **Streamlit** UX (chronological, expandable sources), **README**, **opt-in smokes**.

### Orchestration — supervisor & Agent 1 (Phase 9)

- [ ] **AGT-03**: The turn is implemented as a **LangGraph** graph with **LangChain**-bound tools (including **Tavily**). A **supervisor** step **evaluates** each **candidate answer** against the **user’s original question** and returns a structured decision: **accept** or **reject** (with rationale usable for logging / next-step prompting).
- [ ] **AGT-04**: **Agent 1** (worker) **first** generates a candidate answer using **only RAG / historical retrieval context** (no web tool on that attempt). If the supervisor **rejects**, Agent 1 is invoked again with permission to call the **web search tool**, incorporates returned snippets, and produces a **revised** candidate. If the supervisor **rejects again**, Agent 1 may run **at most one additional** search-and-answer cycle (**second** search iteration). **Maximum two** tool/search iterations after the initial RAG-only attempt.
- [ ] **AGT-05**: If, after **two** search-backed iterations following supervisor rejection, the supervisor still **does not accept** any candidate, the API returns a **fixed Russian user-facing message** stating that a satisfactory answer could not be found (exact copy agreed in plan; no fabricated facts).

### Web search & answer quality (Phase 9)

- [x] **SRCH-01**: **LangChain**-wrapped **Tavily**; query formulation and synthesis via **GigaChat**-driven nodes. *(Phase 8 — behavior folded into Agent 1 + supervisor in v1.3.)*
- [x] **SRCH-02**: **f1api.dev** not used in `/next_message`. *(Phase 8)*
- [ ] **SRCH-03**: Any **accepted** final **`message`** is a **direct Russian answer** to the **original** user question, grounded in the evidence used for that candidate (RAG chunks and/or web snippets). It **must not** be a restatement-only of the search query, a duplicate-only of the user question, or **sources-only** as the sole reply body.

### API contract (Phase 9)

- [ ] **WEB-01**: When the search tool contributed to the accepted answer, the API exposes **structured web evidence** (e.g. queries used, URLs, snippets/titles) in **`details.web`**, distinguishable from **RAG** citations.
- [ ] **API-05**: **`confidence`** is **removed** from all public response shapes: top-level fields, **`details`**, structured answer types, and OpenAPI/examples. Tests and Streamlit **must not** expect or display confidence.

### Streamlit (Phase 10)

- [ ] **UI-04**: Chat history in **chronological order** (oldest at top, **newest** immediately above the composer); turns **appended**.
- [ ] **UI-05**: Assistant **message** text is always visible by default; **sources** (RAG + web) in a **collapsed expander** (or equivalent).
- *(No separate UI-06: absence of confidence follows **API-05**.)*

### Documentation (Phase 11)

- [ ] **DOC-01**: **README**: clone/setup, Python env, index/build if needed, API + Streamlit commands, full **`.env` / `.env.example`** with **acquisition links** for GigaChat, Tavily, and other secrets.

### Quality / integration (Phase 11)

- [ ] **TST-01**: **Pytest** smoke/integration tests (marker + env flag, optional in CI) for live **GigaChat** + **Tavily**; default runs **mocked/offline**.

## v1.2 Requirements (superseded for orchestration — Phase 8 delivered)

- [x] **AGT-01**, **AGT-02**: Linear graph with RAG sufficiency then Tavily — **superseded by AGT-03–AGT-05** in v1.3 (supervisor judges **answers**, not only retrieval scores).

## v1.1 Requirements (milestone complete)

- [x] **GC-01 … GC-03**, **UI-01 … UI-03**, **RUN-01** — delivered; v1.3 updates Streamlit per UI-04/05 and removes confidence per API-05.

## v1 Requirements (baseline — shipped v1.0)

### Q&A Core

- [x] **QNA-01**: User can ask Formula 1 questions in Russian and receive a structured answer.
- [x] **QNA-02**: *Historically:* explicit confidence in responses — **superseded by v1.3 API-05** (citations/sources remain; **no** confidence field).
- [x] **QNA-03**: User receives abstention/degraded response when evidence is insufficient *(terminal failure path in v1.3 aligns with AGT-05)*.

### Historical RAG, Live (v1.0), Auth, Backend

- [x] **RAG-01 … RAG-03**, **LIVE-01 … LIVE-03**, **AUTH-01 … AUTH-02**, **API-01 … API-04** — shipped *(API contract evolves via API-05 in v1.3)*.

## v2 Requirements

Deferred to future release.

### Product Extensions

- **UX-01**: Voice interaction mode (ASR/TTS).
- **PERS-01**: Advanced personalized responses.
- **REM-01**: Reminders and non-spoiler notification mode.
- **DEP-01**: Production Docker Compose stack.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Voice-first assistant | Deferred by product owner |
| Advanced personalization | Deferred until baseline quality is proven |
| **Docker / Compose for v1.1** | Local API + Streamlit |
| **f1api.dev in answer path** | Replaced by Tavily per SRCH-02 |
| **`confidence` in API or UI** | Removed product-wide in v1.3 (API-05) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| QNA-01 | Phase 4 | Complete |
| QNA-02 | Phase 4 | Superseded (API-05) |
| QNA-03 | Phase 4 | Complete |
| RAG-01 … RAG-03 | Phase 3 | Complete |
| LIVE-01 … LIVE-03 | Phase 5 | Complete |
| AUTH-01, AUTH-02 | Phase 1 | Complete |
| API-01 … API-04 | Phase 2 | Complete |
| API-05 | Phase 9 | Planned |
| GC-01 … GC-03 | Phase 6 | Complete |
| UI-01 … UI-03 | Phase 7 | Complete |
| RUN-01 | Phase 7 | Complete |
| AGT-01, AGT-02 | Phase 8 | Superseded (AGT-03–05) |
| SRCH-01, SRCH-02 | Phase 8 | Complete |
| AGT-03 | Phase 9 | Planned |
| AGT-04 | Phase 9 | Planned |
| AGT-05 | Phase 9 | Planned |
| SRCH-03 | Phase 9 | Planned |
| WEB-01 | Phase 9 | Planned |
| UI-04 | Phase 10 | Planned |
| UI-05 | Phase 10 | Planned |
| DOC-01 | Phase 11 | Planned |
| TST-01 | Phase 11 | Planned |

**Coverage (v1.3):** Phases 9–11 planned; Phases 1–8 complete (or superseded where noted).

---
*Last updated: 2026-03-28 — v1.3: supervisor loop, API-05, traceability*
