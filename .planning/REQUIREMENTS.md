# Requirements: F1 Assistant (GigaChat + LangGraph)

**Defined:** 2026-03-26  
**Core Value:** The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

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

### Live API + Reliability

- [x] **LIVE-01**: User receives live-enriched answer when RAG context is insufficient and live data is required.
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

**Coverage (v1.1):** Phases 6–7 requirements complete.

---
*Last updated: 2026-03-27 — Phase 7 complete; UI + RUN requirements verified*
