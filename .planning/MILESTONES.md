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

### v1.4 — Single-pass web, unified provenance UI

**Completed:** 2026-03-28  
**Phases:** **12–13** (**AGT-06, AGT-07, SRCH-04, WEB-02**, **UI-04–06**).  
**Outcome:** Один Tavily + один optional fetch; единый блок происхождения в Streamlit.

### v1.5 — F1DB RAG (Phase 14); Phase 15 skipped; docs → v1.6

**Closed (partial):** 2026-03-28  
**Phases:** **14** complete (**RAG-08, RAG-09**); **15** (**AGT-08, AGT-09, SRCH-05**) **skipped** by owner decision; бывшая **16** (docs) перенесена в **v1.6 Phase 19**.  
**Outcome:** Whitelist RAG, датасет из БД, **ru-en-RoSBERTa** — по работе владельца; веб-цепочка остаётся как в **Phase 12**.

---

## Active

### v1.6 — Real-time clock, F1 schedule tools, then docs (phases 17–19)

**Started:** 2026-03-28  
**Focus:** **TimeAPI.io** + **FastF1** + worker **tools** (**17–18**); **README / README_DETAILED / smokes** (**19**, черновик допустим).
