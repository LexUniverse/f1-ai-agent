# Requirements: F1 Assistant (GigaChat + LangGraph)

**Defined:** 2026-03-26 / **v1.4 scoped:** 2026-03-28  
**Core Value:** The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## v1.4 Requirements (milestone active)

**Supersedes** the unfinished **v1.3 roadmap phases 10–11** by merging Streamlit + docs with new orchestration and UI work. Phases **12–14** on the roadmap.

### Supervisor & acceptance (Phase 12)

- [x] **AGT-06**: **Accept/reject** is determined **only** by the **supervisor LLM** (GigaChat JSON). **Audit** the codebase for any **numeric thresholds** (e.g. legacy 0.55-style gates) on the **accept path**; remove or document if unrelated to the removed product `confidence` field. **Tune** parse-failure policy (currently conservative `False`) so real API errors are distinguishable from **avoidable false rejects**.
- [x] **AGT-07**: After the **initial RAG-only** candidate, the worker may use the **web tool at most once per turn** (one Tavily query). **No second** Tavily iteration. **Deepening** happens inside that pass: **rank** returned URLs, assess **titles/snippets**; if insufficient, **fetch exactly one** operator-chosen URL (HTTP, bounded) and incorporate extracted text into **one** revised candidate before the supervisor sees it again. If still rejected, **AGT-05** terminal message (same user-facing copy unless plan agrees a tweak).

### Search & synthesis (Phase 12)

- [x] **SRCH-04**: Worker **selects** the best-matching result(s) from the Tavily list for the user question; **prefers** an answer from **titles/snippets** when they suffice; **escalates** to **single-page** content only when needed.

### API / provenance (Phase 12–13)

- [x] **WEB-02**: Response **`details`** expose a **single structured surface** suitable for UI: **RAG** evidence (snippets/source ids) and **web** (query, URLs, titles, snippets, optional **fetch** metadata) without duplicating the same URLs in multiple unrelated keys. *(Extends **WEB-01**.)*

### Streamlit (Phase 13)

- [ ] **UI-04**: Chat history **chronological** (oldest top, **newest** above composer); turns **appended**.
- [ ] **UI-05**: Assistant **message** body always visible; **no** confidence UI (**API-05**).
- [ ] **UI-06**: **One** collapsed **«Происхождение ответа»** (or agreed label) expander containing **RAG context**, **web** provenance, and **synthesis route / metadata** — **no** separate duplicate «Источники» blocks + separate web JSON expander + vague «Синтез»-only labels for the same content.

### Documentation & quality (Phase 14)

- [ ] **DOC-01**: **README**: clone/setup, env, index/build, API + Streamlit commands, **`.env` / `.env.example`** with acquisition links.
- [ ] **TST-01**: **Pytest** opt-in smokes (marker + env) for live GigaChat/Tavily; default CI **offline/mocked**.

---

## v1.3 Requirements (milestone core — delivered Phase 9)

Scoped 2026-03-28 — supervisor loop, no product confidence, `details.web`. *(Phases 10–11 moved to v1.4.)*

### Orchestration — supervisor & Agent 1 (Phase 9)

- [x] **AGT-03**: LangGraph + LangChain tools; **supervisor** evaluates **candidate answer** vs **user question**; accept/reject.
- [x] **AGT-04**: *(v1.3 wording)* RAG-first, then **up to two** Tavily-backed revisions — **superseded by AGT-07** in v1.4 (one Tavily + optional fetch).
- [x] **AGT-05**: Fixed Russian terminal message after exhausted search-backed attempts — **still required**; **exhaustion** definition updates to **AGT-07** (one Tavily pass).

### Web search & answer quality (Phase 9)

- [x] **SRCH-01**, **SRCH-02** — Phase 8 / folded into Agent 1.
- [x] **SRCH-03**: Accepted **`message`** answers the **original** question; not query-echo / sources-only.

### API contract (Phase 9)

- [x] **WEB-01**: **`details.web`** when search contributed.
- [x] **API-05**: No **`confidence`** in public shapes.

### Streamlit / docs (were Phase 10–11 — now v1.4)

- See **UI-04, UI-05, UI-06, DOC-01, TST-01** above.

## v1.2 Requirements (superseded for orchestration)

- [x] **AGT-01**, **AGT-02** — superseded by AGT-03–05 / AGT-06–07.

## v1.1 / v1.0

- [x] Baseline QNA, RAG, LIVE, AUTH, API, GC, UI-01–03, RUN-01 — shipped; **QNA-02** superseded by API-05.

## v2 Requirements

Deferred (voice, personalization, Docker, etc.) — unchanged.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Voice-first assistant | Deferred |
| Advanced personalization | Deferred |
| Docker / Compose for v1.x | Local API + Streamlit |
| f1api.dev in answer path | Tavily path |
| **`confidence` in API or UI** | API-05 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| QNA-01 … QNA-03, RAG-*, LIVE-*, AUTH-*, API-01–04 | 1–5 | Complete / superseded |
| GC-*, UI-01–03, RUN-01 | 6–7 | Complete |
| AGT-01–02, SRCH-01–02 | 8 | Complete / superseded |
| AGT-03, AGT-05, SRCH-03, WEB-01, API-05 | 9 | Complete |
| AGT-04 (v1.3 two Tavily) | 9 | **Superseded** → AGT-07 |
| UI-04, UI-05 | 10 → **13** | Planned (v1.4) |
| DOC-01, TST-01 | 11 → **14** | Planned (v1.4) |
| AGT-06, AGT-07, SRCH-04 | 12 (wave 1) | Planned |
| WEB-02 | 12 (wave 2) | Planned |
| UI-06 | 13 | Planned |

**Coverage (v1.4):** Phases **12–14** planned; Phases **1–9** complete (subject to v1.4 supersession of AGT-04).

---
*Last updated: 2026-03-28 — v1.4 milestone: REQ-IDs AGT-06/07, SRCH-04, WEB-02, UI-06, DOC-01, TST-01*
