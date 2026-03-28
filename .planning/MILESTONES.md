# Milestones: F1 Assistant

## Completed

### v1.0 — Trust-first API, RAG, RU contracts, live enrichment

**Completed:** 2026-03-27  
**Phases:** 1–5 (access control → async API → historical RAG → RU Q&A reliability → live enrichment & freshness).  
**Outcome:** FastAPI backend with deterministic structured Russian answers, f1db/Chroma retrieval, conditional f1api.dev live branch, explicit degraded modes.

### v1.1 — GigaChat classic RAG + Streamlit (local run)

**Completed:** 2026-03-27  
**Phases:** 6–7 (GigaChat chunk-grounded RAG + template fallback; Streamlit UI + local runbook).  
**Outcome:** GigaChat synthesis path, operator Streamlit client, documented `python api.py` + Streamlit (no Docker).

### v1.2 — GigaChat supervisor — RAG → Tavily (LangGraph)

**Completed (scope delivered):** 2026-03-28  
**Phases:** 1–8 (through LangGraph + Tavily; f1api removed from `/next_message`).  
**Outcome:** Compiled graph, retrieval sufficiency gate, GigaChat web path, bounded search/degraded RU copy.

_Note: Linear Phase-8 orchestration is **replaced** in v1.3 by a **supervisor–Agent 1** loop._

### v1.3 — Supervisor–agent graph, confidence removed (core shipped)

**Completed (core):** 2026-03-28  
**Phases:** 9 (supervisor loop, ≤2 Tavily, AGT-05, API-05, WEB-01).  
**Outcome:** LangGraph supervisor + Agent 1, no `confidence` in API, `details.web`.  
**Deferred / superseded:** Original roadmap phases **10–11** (Streamlit polish, README/smokes) **merged into v1.4** together with orchestration and UI fixes.

---

## Active

### v1.4 — Supervisor tuning, single-pass deep web, unified provenance UI

**Started:** 2026-03-28  
**Focus:** Stop **false AGT-05** (audit supervisor + any hidden gates; **only GigaChat** judges acceptance). **One Tavily query per turn** after RAG rejection: rank results, **title-first** answer, **optional single-page fetch** if titles insufficient — **no second search iteration**. **Streamlit:** one **collapsed** provenance block (RAG + web + route metadata), **no duplicated** «Источники», clearer Russian labels. **README + opt-in smokes** (carry DOC-01, TST-01).
