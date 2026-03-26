# Stack Research

**Domain:** Agentic RAG assistant for Formula 1 (RU-first async chat)
**Researched:** 2026-03-26
**Confidence:** MEDIUM-HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12.x | Primary runtime | Best ecosystem fit for LangGraph, FastAPI, and retrieval tooling; stable async performance and broad AI SDK support. |
| FastAPI | 0.135.2 | Backend API and async orchestration entrypoints | Production-standard Python API framework for typed async endpoints, validation, and OpenAPI-first contracts. |
| LangGraph | 1.1.3 | Agent orchestration graph (planner/rag/tool/evaluator) | Most mature graph-native runtime for agent state, branching, checkpointing, and resilient multi-step flows. |
| Streamlit | 1.55.0 | Operator-facing and user chat UI | Fastest way to ship Python-native chat UX with session state and deployment simplicity for early-stage products. |
| ChromaDB | 1.5.5 | Vector + metadata retrieval store | Strong default for self-hosted RAG MVPs: fast setup, metadata filters, hybrid retrieval capabilities, and low ops burden. |
| GigaChat SDK | 0.2.0 | Primary LLM provider client | Direct model access for RU-centric assistant behavior and provider-native capabilities. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-gigachat | 0.5.0 | LangChain/LangGraph model adapter for GigaChat | Use when you want standardized model abstractions and easier prompt/tool interoperability in graph nodes. |
| langchain-core | 1.2.22 | Shared Runnable/message abstractions | Use for consistent chain/node interfaces and tool-call schema flow across graph components. |
| pydantic | 2.12.5 | Strict I/O schemas and structured outputs | Use for all API contracts, node state, tool payloads, and validation gates before returning answers. |
| uvicorn | 0.42.0 | ASGI server for FastAPI | Use in local/dev and simple production container setups where Gunicorn is unnecessary overhead. |
| httpx | 0.28.1 | Async HTTP client for live F1 APIs | Use for resilient sports API calls with timeout/retry policy and explicit degraded-mode behavior. |
| langsmith | 0.7.22 | Tracing/observability for agent runs | Use when you need node-level traces, latency hotspots, and prompt/tool debugging in production. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Ruff | Lint + formatting | Replace flake8/isort/black stack with one fast toolchain; enforce in CI. |
| Pytest | Test framework | Cover graph-node unit tests, retrieval relevance tests, and end-to-end API contracts. |
| Docker + Compose | Deployment packaging | Keep backend and Streamlit UI as separate services with explicit env/network boundaries. |

## Installation

```bash
# Core
pip install "fastapi==0.135.2" "uvicorn==0.42.0" "streamlit==1.55.0"
pip install "langgraph==1.1.3" "langchain-core==1.2.22"
pip install "chromadb==1.5.5"
pip install "gigachat==0.2.0" "langchain-gigachat==0.5.0"

# Supporting
pip install "pydantic==2.12.5" "httpx==0.28.1" "langsmith==0.7.22"

# Dev dependencies
pip install -D "pytest>=8.0.0" "ruff>=0.6.0"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| ChromaDB | Qdrant | Use Qdrant when you need heavier horizontal scaling and stricter production vector DB operations from day one. |
| Streamlit | Next.js + FastAPI frontend API split | Use when you need multi-role product UI, custom routing, and advanced frontend performance beyond chat MVP needs. |
| LangGraph | ADK/Crew-style orchestration frameworks | Use only if your team explicitly prefers role-agent abstractions over graph/state-machine control. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Flask for this backend | You will rebuild typed validation, async patterns, and OpenAPI workflows that FastAPI already provides. | FastAPI |
| SQLite-only retrieval hacks (no vector DB) | Poor semantic retrieval quality and brittle scaling for RAG over F1 history corpora. | ChromaDB (or Qdrant if scale-first) |
| Legacy LangChain 0.x patterns as primary architecture | Outdated APIs and migration churn increase maintenance risk in agentic systems. | LangGraph 1.x + langchain-core 1.x |
| Blocking HTTP clients in async graph nodes (e.g., `requests`) | Can block event loop and increase latency variance for live sports API calls. | httpx async client |

## Stack Patterns by Variant

**If accuracy and observability are top priority (recommended default):**
- Use LangGraph + LangSmith + Pydantic strict schemas.
- Because graph checkpoints and traceability reduce silent failure and hallucination risks.

**If ultra-fast MVP delivery is top priority:**
- Use Streamlit UI + FastAPI + Chroma local persistence first.
- Because this minimizes frontend and infra complexity while preserving migration paths.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `fastapi==0.135.2` | `pydantic==2.12.5` | Current FastAPI line is Pydantic v2-native; keep both on modern major versions. |
| `langgraph==1.1.3` | `langchain-core==1.2.22` | Keep LangGraph and LangChain-core on current 1.x generation to avoid API drift. |
| `langchain-gigachat==0.5.0` | `gigachat==0.2.0` | Prefer matched current releases to reduce adapter/provider mismatch risk. |

## Sources

- https://fastapi.tiangolo.com/ — official framework docs and deployment guidance (MEDIUM confidence, official)
- https://docs.langchain.com/langgraph-platform/ — LangGraph/LangSmith deployment/runtime docs (MEDIUM confidence, official)
- https://docs.trychroma.com/ — Chroma product/docs landing and retrieval capabilities (MEDIUM confidence, official)
- https://docs.streamlit.io/ — Streamlit official docs and release surface (MEDIUM confidence, official)
- PyPI package indexes via `pip index versions` for `fastapi`, `langgraph`, `chromadb`, `streamlit`, `gigachat`, `langchain-gigachat`, `langchain-core`, `langsmith`, `pydantic`, `uvicorn`, `httpx` (HIGH confidence for version numbers)

---
*Stack research for: Formula 1 async chat assistant (GigaChat + LangGraph + RAG)*
*Researched: 2026-03-26*
