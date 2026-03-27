# Requirements: F1 Assistant (GigaChat + LangGraph)

**Defined:** 2026-03-26 / **v1.2 scoped:** 2026-03-27  
**Core Value:** The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## v1.2 Requirements (milestone active)

Scoped 2026-03-27 — **LangGraph** supervisor with **GigaChat**; **RAG sufficiency** → **Tavily (LangChain)**; remove **f1 API** live path; **README** + **credential smoke tests**.

### Agent orchestration (Phase 8)

- [ ] **AGT-01**: The assistant processes each user turn through a **LangGraph** (or equivalent compiled graph) with a **supervisor** node that can delegate to **RAG** and **tool** subgraphs; **GigaChat** is the primary model for routing, Tavily query formulation, and final synthesis (template/disclosure fallback on LLM outage preserved where applicable).
- [ ] **AGT-02**: After retrieval, the system **evaluates whether RAG evidence is sufficient** to answer (explicit rules and/or LLM judge); only if **not sufficient** does it invoke **Tavily**.

### Web search & deprecation (Phase 8–9)

- [ ] **SRCH-01**: When RAG is insufficient, the assistant uses **LangChain**-wrapped **Tavily Search**: **GigaChat** produces a **search query**, results are retrieved, and the model **synthesizes a Russian answer** grounded in returned sources (URLs surfaced for citations).
- [ ] **SRCH-02**: The **f1api.dev** (or dedicated F1 REST) client **is not used** in the `/next_message` answer pipeline; code paths and dependencies are removed or gated off in favor of the Tavily branch.

### API / UI contract (Phase 9)

- [ ] **WEB-01**: When web search is used, the API exposes **structured web evidence** (e.g. query, source URLs, snippets/metadata) in `details` (or successor fields) so clients can display provenance; **Streamlit** is updated to show **web** sources alongside RAG citations (migrate away from **`details.live`** as the primary freshness signal where appropriate).

### Documentation (Phase 10)

- [ ] **DOC-01**: **README** documents **clone/setup**, **Python environment**, **index/build** if required, how to run **API** and **Streamlit**, and a complete **`.env` / `.env.example` checklist** including **GigaChat**, **Tavily**, and other required keys **with links or instructions to obtain each key**.

### Quality / integration (Phase 10)

- [ ] **TST-01**: **Pytest** includes **smoke or integration** tests (clearly marked, **optional in CI** via marker/env flag) that verify **GigaChat** responds with valid credentials and that **Tavily** (and other required `.env` secrets) are **accepted by upstream APIs** (not merely present); default unit runs remain **mocked/offline**.

## v1.1 Requirements (milestone complete)

Scoped 2026-03-27 — **local run only (no Docker)**; **Phase 6** classic RAG via GigaChat; **Phase 7** Streamlit.

### GigaChat classic RAG (Phase 6)

- [x] **GC-01**: When historical retrieval returns evidence, the assistant generates the Russian answer with **GigaChat** using a prompt that includes **retrieved chunks** (retrieval → prompt → LLM → RU answer), preserving traceable citations in API `details`.
- [x] **GC-02**: When **GigaChat is unavailable or errors**, `/next_message` **falls back** to deterministic **template** synthesis (equivalent behavior to pre-6 template path) with explicit degraded signaling where appropriate — no silent substitution of fabricated facts.
- [x] **GC-03**: Primary LLM RAG implementation lives in **`src/answer/gigachat_rag.py`**; **`src/answer/russian_qna.py`** is removed or reduced to **shared helpers / template fallback only** (per implementation plan).

### Streamlit UI (Phase 7)

- [x] **UI-01**: User provides **access_code** and **question**; client calls **`/start_chat`** and stores **`session_id`**.
- [x] **UI-02**: Client **polls `/message_status`** until a terminal state, then retrieves the assistant payload via **`/next_message`** consistent with the async contract.
- [x] **UI-03**: UI displays **`message`**, **confidence**, **citations** (sources), and **`details.live`** when present.

### Local run (Phase 7)

- [x] **RUN-01**: Documentation describes **local** execution: API via **`python api.py`** (or the documented equivalent) and the Streamlit app via **`streamlit run …`** — **Docker not required** for v1.1.

## v1 Requirements (baseline — shipped v1.0)

Requirements for the initial backend milestone. Traceability references Phases 1–5.

### Q&A Core

- [x] **QNA-01**: User can ask Formula 1 questions in Russian and receive a structured answer.
- [x] **QNA-02**: User answer includes explicit confidence level and source citations.
- [x] **QNA-03**: User receives abstention/degraded response when evidence is insufficient.

### Historical RAG

- [x] **RAG-01**: User can receive answers grounded in f1db historical data indexed in ChromaDB.
- [x] **RAG-02**: User queries are matched against RU/EN entity aliases (drivers, teams, races).
- [x] **RAG-03**: User receives traceable retrieved context references used for final answer synthesis.

### Live API + Reliability (v1.0 – superseded for enrichment by v1.2 Tavily)

- [x] **LIVE-01**: User receives live-enriched answer when RAG context is insufficient and live data is required. *(v1.0–v1.1: f1api; v1.2 replaces enrichment with Tavily — see SRCH-01.)*
- [x] **LIVE-02**: User receives clear degraded-mode message when live API is unavailable.
- [x] **LIVE-03**: User answer includes freshness metadata (`as_of`) for live-dependent responses.

### Authentication

- [x] **AUTH-01**: User can access assistant only with a valid personal access code from allowlist.
- [x] **AUTH-02**: User with invalid code is denied access with an explicit unauthorized message.

### Backend/API

- [x] **API-01**: Client can start a session via async endpoint equivalent to `/start_chat`.
- [x] **API-02**: Client can poll status via async endpoint equivalent to `/message_status`.
- [x] **API-03**: Client can request next response via async endpoint equivalent to `/next_message`.
- [x] **API-04**: API validates structured input/output contracts via Pydantic models.

## v2 Requirements

Deferred to future release. Tracked but not in the current roadmap milestone.

### Product Extensions

- **UX-01**: User can enable voice interaction mode (ASR/TTS).
- **PERS-01**: User can receive advanced personalized responses from behavior-based profile.
- **REM-01**: User can configure reminders and non-spoiler notification mode.
- **DEP-01**: System is deployable with production Docker Compose stack.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Voice-first assistant | Deferred by product owner |
| Advanced personalization | Deferred until baseline quality is proven |
| **Docker / Compose for v1.1** | **Milestone decision — v1.1 uses local API + Streamlit only** |
| **f1api.dev in v1.2+ answer path** | Replaced by Tavily web search per SRCH-02 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| QNA-01 | Phase 4 | Complete |
| QNA-02 | Phase 4 | Complete |
| QNA-03 | Phase 4 | Complete |
| RAG-01 | Phase 3 | Complete |
| RAG-02 | Phase 3 | Complete |
| RAG-03 | Phase 3 | Complete |
| LIVE-01 | Phase 5 | Complete |
| LIVE-02 | Phase 5 | Complete |
| LIVE-03 | Phase 5 | Complete |
| AUTH-01 | Phase 1 | Complete |
| AUTH-02 | Phase 1 | Complete |
| API-01 | Phase 2 | Complete |
| API-02 | Phase 2 | Complete |
| API-03 | Phase 2 | Complete |
| API-04 | Phase 2 | Complete |
| GC-01 | Phase 6 | Complete |
| GC-02 | Phase 6 | Complete |
| GC-03 | Phase 6 | Complete |
| UI-01 | Phase 7 | Complete |
| UI-02 | Phase 7 | Complete |
| UI-03 | Phase 7 | Complete |
| RUN-01 | Phase 7 | Complete |
| AGT-01 | Phase 8 | Planned |
| AGT-02 | Phase 8 | Planned |
| SRCH-01 | Phase 8 | Planned |
| SRCH-02 | Phase 8 | Planned |
| WEB-01 | Phase 9 | Planned |
| DOC-01 | Phase 10 | Planned |
| TST-01 | Phase 10 | Planned |

**Coverage (v1.1):** Phases 6–7 requirements complete.  
**Coverage (v1.2):** Phases 8–10 — requirements defined; execution pending.

---
*Last updated: 2026-03-27 — v1.2 requirements added (phases 8–10)*
