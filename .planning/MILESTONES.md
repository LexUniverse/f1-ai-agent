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

_Note: Linear Phase-8 orchestration is **replaced** in v1.3 by a **supervisor–Agent 1** loop. Originally scoped README + smokes + WEB contract moved to **v1.3 phases 9–11**._

---

## Active

### v1.3 — Supervisor–agent graph, confidence removed, UX & docs

**Started:** 2026-03-28  
**Focus:** **LangGraph + LangChain**: **supervisor** accepts/rejects **candidate answers**; **Agent 1** answers **RAG-only** first, then uses **Tavily tool** up to **two** times on supervisor demand; **fixed RU failure** if still inadequate. **`confidence` removed from entire API and UI.** **`details.web`**; Streamlit **chronological** chat, **message first**, **expandable sources**; **README** + **opt-in pytest** smokes.
