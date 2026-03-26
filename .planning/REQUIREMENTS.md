# Requirements: F1 Assistant (GigaChat + LangGraph)

**Defined:** 2026-03-26
**Core Value:** The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Q&A Core

- [ ] **QNA-01**: User can ask Formula 1 questions in Russian and receive a structured answer.
- [ ] **QNA-02**: User answer includes explicit confidence level and source citations.
- [ ] **QNA-03**: User receives abstention/degraded response when evidence is insufficient.

### Historical RAG

- [ ] **RAG-01**: User can receive answers grounded in f1db historical data indexed in ChromaDB.
- [ ] **RAG-02**: User queries are matched against RU/EN entity aliases (drivers, teams, races).
- [ ] **RAG-03**: User receives traceable retrieved context references used for final answer synthesis.

### Live API + Reliability

- [ ] **LIVE-01**: User receives live-enriched answer when RAG context is insufficient and live data is required.
- [ ] **LIVE-02**: User receives clear degraded-mode message when live API is unavailable.
- [ ] **LIVE-03**: User answer includes freshness metadata (`as_of`) for live-dependent responses.

### Authentication

- [ ] **AUTH-01**: User can access assistant only with a valid personal access code from allowlist.
- [ ] **AUTH-02**: User with invalid code is denied access with explicit unauthorized message.

### Backend/API

- [ ] **API-01**: Client can start a session via async endpoint equivalent to `/start_chat`.
- [ ] **API-02**: Client can poll status via async endpoint equivalent to `/message_status`.
- [ ] **API-03**: Client can request next response via async endpoint equivalent to `/next_message`.
- [ ] **API-04**: API validates structured input/output contracts via Pydantic models.

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Product Extensions

- **UX-01**: User can enable voice interaction mode (ASR/TTS).
- **PERS-01**: User can receive advanced personalized responses from behavior-based profile.
- **REM-01**: User can configure reminders and non-spoiler notification mode.
- **DEP-01**: System is deployable with production Docker Compose stack.

## Out of Scope

Explicitly excluded in v1.

| Feature | Reason |
|---------|--------|
| Voice-first assistant | Explicitly deferred by product owner to keep v1 focused on trust and accuracy |
| Advanced personalization | Deferred until baseline quality and reliability are proven |
| Full Docker production packaging | Deferred by scope decision for current v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| QNA-01 | Phase 4 | Pending |
| QNA-02 | Phase 4 | Pending |
| QNA-03 | Phase 4 | Pending |
| RAG-01 | Phase 3 | Pending |
| RAG-02 | Phase 3 | Pending |
| RAG-03 | Phase 3 | Pending |
| LIVE-01 | Phase 5 | Pending |
| LIVE-02 | Phase 5 | Pending |
| LIVE-03 | Phase 5 | Pending |
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| API-01 | Phase 2 | Pending |
| API-02 | Phase 2 | Pending |
| API-03 | Phase 2 | Pending |
| API-04 | Phase 2 | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✅

---
*Requirements defined: 2026-03-26*
*Last updated: 2026-03-26 after roadmap traceability mapping*
