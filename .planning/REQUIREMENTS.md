# Requirements: F1 Assistant (GigaChat + LangGraph)

**Defined:** 2026-03-26 / **v1.3 scoped:** 2026-03-28  
**Core Value:** The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## v1.3 Requirements (milestone active)

Scoped 2026-03-28 — **Web synthesis fidelity** (answer the **original** user question from Tavily snippets), **`details.web`** contract, **Streamlit** layout/UX (chronological turns, expandable sources, no confidence chrome), **README** + **opt-in credential smokes**.

### Web search & synthesis (Phase 9)

- [x] **SRCH-01**: When RAG is insufficient, the assistant uses **LangChain**-wrapped **Tavily Search**: **GigaChat** produces a **search query**, results are retrieved, and the model **synthesizes a Russian answer** grounded in returned sources (URLs surfaced for citations). *(Phase 8 — shipped; v1.3 tightens outcome quality.)*
- [x] **SRCH-02**: The **f1api.dev** (or dedicated F1 REST) client **is not used** in the `/next_message` answer pipeline. *(Phase 8)*
- [ ] **SRCH-03**: After Tavily returns non-empty results, the **primary user-visible `message`** is a **direct Russian answer to the user’s original question**, grounded in returned snippets. It **must not** substitute the answer with a restatement of the search query, a duplicate of the user question only, or a **sources-only** block as the sole reply. *(Phase 9)*

### API / provenance (Phase 9)

- [ ] **WEB-01**: When web search is used, the API exposes **structured web evidence** (e.g. search query, source URLs, snippets/metadata) in **`details.web`** (alongside existing fields) so clients can render provenance; **RAG** citations remain distinguishable from **web** sources.

### Streamlit (Phase 10)

- [ ] **UI-04**: Chat history is shown in **chronological order** (oldest at top, **newest directly above** the composer); new user and assistant turns are **appended**, not prepended.
- [ ] **UI-05**: For each assistant turn, the UI shows the **main answer text** by default; **sources** (`sources_block_ru` and/or structured web list) appear inside a **collapsed expander** (or equivalent) so the operator can open them on demand.
- [ ] **UI-06**: The Streamlit UI **does not display** confidence tier/score for assistant replies (**until** a future milestone recalibrates meaningful scores for RAG and web paths).

### Documentation (Phase 11)

- [ ] **DOC-01**: **README** documents **clone/setup**, **Python environment**, **index/build** if required, how to run **API** and **Streamlit**, and a complete **`.env` / `.env.example` checklist** including **GigaChat**, **Tavily**, and other required keys **with links or instructions to obtain each key**.

### Quality / integration (Phase 11)

- [ ] **TST-01**: **Pytest** includes **smoke or integration** tests (clearly marked, **optional in CI** via marker/env flag) that verify **GigaChat** responds with valid credentials and that **Tavily** (and other required `.env` secrets) are **accepted by upstream APIs** (not merely present); default unit runs remain **mocked/offline**.

## v1.2 Requirements (architecture shipped — phases 1–8)

### Agent orchestration

- [x] **AGT-01**: LangGraph supervisor with GigaChat; delegation to RAG and tool nodes. *(Phase 8)*
- [x] **AGT-02**: RAG sufficiency evaluation before Tavily. *(Phase 8)*

## v1.1 Requirements (milestone complete)

### GigaChat classic RAG (Phase 6)

- [x] **GC-01** … **GC-03** — see traceability table.

### Streamlit UI (Phase 7)

- [x] **UI-01** … **UI-03** — delivered; **UI-04–06** supersede Streamlit display expectations for v1.3.

### Local run (Phase 7)

- [x] **RUN-01**: Local API + Streamlit documented.

## v1 Requirements (baseline — shipped v1.0)

### Q&A Core

- [x] **QNA-01**: User can ask Formula 1 questions in Russian and receive a structured answer.
- [x] **QNA-02**: User answer includes explicit confidence level and source citations *(API may still emit confidence; **Streamlit hides** per UI-06 until recalibration).*
- [x] **QNA-03**: User receives abstention/degraded response when evidence is insufficient.

### Historical RAG, Live (v1.0), Auth, Backend

- [x] **RAG-01** … **RAG-03**, **LIVE-01** … **LIVE-03**, **AUTH-01** … **AUTH-02**, **API-01** … **API-04** — shipped.

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
| **Docker / Compose for v1.1** | v1.1 milestone decision — local API + Streamlit |
| **f1api.dev in answer path** | Replaced by Tavily per SRCH-02 |
| **Confidence UI without calibration** | Misleading (flat web-path score); hidden per UI-06 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| QNA-01 | Phase 4 | Complete |
| QNA-02 | Phase 4 | Complete |
| QNA-03 | Phase 4 | Complete |
| RAG-01 … RAG-03 | Phase 3 | Complete |
| LIVE-01 … LIVE-03 | Phase 5 | Complete |
| AUTH-01, AUTH-02 | Phase 1 | Complete |
| API-01 … API-04 | Phase 2 | Complete |
| GC-01 … GC-03 | Phase 6 | Complete |
| UI-01 … UI-03 | Phase 7 | Complete |
| RUN-01 | Phase 7 | Complete |
| AGT-01, AGT-02 | Phase 8 | Complete |
| SRCH-01, SRCH-02 | Phase 8 | Complete |
| SRCH-03 | Phase 9 | Planned |
| WEB-01 | Phase 9 | Planned |
| UI-04 | Phase 10 | Planned |
| UI-05 | Phase 10 | Planned |
| UI-06 | Phase 10 | Planned |
| DOC-01 | Phase 11 | Planned |
| TST-01 | Phase 11 | Planned |

**Coverage (v1.3):** Phases 9–11 planned; Phases 1–8 complete.

---
*Last updated: 2026-03-28 — Milestone v1.3 requirements*
