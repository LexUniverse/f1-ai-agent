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
**Outcome:** Compiled graph, sufficiency gate, GigaChat web path, bounded search/degraded RU copy.

_Note: Originally scoped README + credential smokes + WEB contract as phases 9–10; **rescoped into v1.3** as phases 9–11 with additional synthesis + Streamlit UX work._

---

## Active

### v1.3 — Web answer fidelity, Streamlit UX, docs & smokes

**Started:** 2026-03-28  
**Focus:** Fix **Tavily → synthesis** so replies **answer the user’s original question** (not search-query echo); **`details.web`** in API; Streamlit **chronological** chat, **message first** + **expandable sources**, **no confidence** in UI; **README** / **`.env`** catalog and **opt-in pytest** smokes for GigaChat + Tavily.
