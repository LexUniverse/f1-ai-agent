# Project Research Summary

**Project:** F1 Assistant (GigaChat + LangGraph)  
**Domain:** Multi-agent orchestration — RAG + web search (Tavily)  
**Researched:** 2026-03-27  
**Confidence:** HIGH (architecture/features); MEDIUM (exact library pins)

## Executive Summary

v1.2 replaces the **f1api.dev** enrichment path with **Tavily** behind **LangChain tools**, orchestrated by a **LangGraph supervisor** with **GigaChat** as the core reasoning model. The user-facing async API and Streamlit client should keep **structured Russian answers**, **confidence**, and **citations**, but citations may blend **RAG chunk refs** and **web URLs**.

Risks are **web-source hallucination**, **Tavily cost/latency**, and **async/event-loop blocking** from LLM calls — mitigate with caps, explicit URL grounding in prompts/UI, and thread offload in FastAPI.

## Key Findings

### Recommended Stack

Pin **langgraph** and **langchain** / **langchain-community** compatibly; use **Tavily** via LangChain’s Tavily integration; keep **gigachat** for routing, query formulation, and synthesis.

**Core technologies:**
- **LangGraph** — supervisor + branch nodes (RAG vs tools).
- **LangChain + community** — Tavily tool wrapper.
- **GigaChat** — existing SDK; extend prompts for search-query generation and merged evidence.

### Expected Features

**Must have (table stakes):**
- RAG retrieval + **explicit sufficiency evaluation** before web search.
- Tavily path: **LLM-crafted query** → results → **RU answer** with source URLs.
- **Remove F1 REST** from answer path.
- **README** with `.env` keys and acquisition links; **smoke/integration tests** for keys + GigaChat.

**Should have:**
- Parallel supervisor fan-out where latency allows (classification + RAG).

**Defer:**
- Multi-query Tavily refinement loops beyond one reformulation.
- New vector DB or second LLM vendor.

### Architecture Approach

FastAPI preserves sessions; **inner loop** becomes a **compiled LangGraph**: supervisor → RAG → gate → (optional Tavily) → unified synthesizer → existing response envelope. Deprecate live-specific fields in favor of **web/external** metadata where needed.

**Major components:**
1. **Supervisor** — intent + routing.
2. **RAG node** — current Chroma/f1db pipeline.
3. **Tool node** — Tavily via LangChain.
4. **Answer node** — GigaChat + template fallback.

### Critical Pitfalls

1. Uncited or over-trusted Tavily snippets → enforce URL visibility and conservative confidence.
2. Unbounded tool calls → cap per turn.
3. Flaky CI on live APIs → mocks by default, opt-in integration marker.
4. Breaking Streamlit on `details.live` → migrate schema with UI in same milestone.

### Roadmap Implications

- **Phase 8:** Graph skeleton, sufficiency gate, Tavily integration, remove f1api path.
- **Phase 9:** Response schema + Streamlit alignment, reliability hardening.
- **Phase 10:** README expansion, `.env.example`, pytest markers for integration smokes.
