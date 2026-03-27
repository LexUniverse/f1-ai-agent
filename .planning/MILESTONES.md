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

---

## Active

### v1.2 — GigaChat supervisor — RAG → Tavily (LangGraph) + README + key smokes

**Started:** 2026-03-27  
**Focus:** LangGraph supervisor (GigaChat core), RAG sufficiency gate, LangChain Tavily tool (remove f1 API path), expanded README (`.env` + key sources), pytest smokes for GigaChat and API keys.
