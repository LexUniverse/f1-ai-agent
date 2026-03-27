# Stack Research

**Domain:** F1 assistant — LangGraph supervisor, GigaChat, RAG, Tavily via LangChain  
**Researched:** 2026-03-27  
**Confidence:** MEDIUM (verify versions at implementation time)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **langgraph** | ^0.2.x (align with project lockfile) | Supervisor + stateful multi-node orchestration | Native fit for RAG → tool branch routing; checkpointing optional later |
| **langchain** | ^0.3.x (align w/ LangGraph) | Tool abstractions, Tavily integration | `TavilySearchResults` / community tool wrappers reduce bespoke HTTP |
| **langchain-community** | match LangChain | Tavily tool, third-party loaders | Standard pattern for search tools |
| **gigachat** | existing (`0.2.0` in project) | LLM for routing, query formulation, synthesis | Already integrated; keep single vendor for core reasoning where possible |
| **tavily-python** | optional (LangChain may bundle) | Direct API if bypassing LC | Fallback if LC wrapper lags |

### Supporting Libraries

| Library | Purpose | When to Use |
|---------|---------|-------------|
| **httpx** | Async HTTP for FastAPI graph | Already in stack |
| **pydantic** v2 | Response contracts | Preserve `/next_message` shapes |

### Environment

| Variable | Purpose |
|----------|---------|
| `GIGACHAT_*` / existing | GigaChat credentials (see README) |
| `TAVILY_API_KEY` | Tavily search |
| Existing Chroma / index paths | RAG unchanged |

## Installation Notes

- Pin **LangGraph + LangChain** versions together to avoid resolver conflicts.
- Avoid duplicating Tavily: one path — either LC tool only or thin wrapper.

## What NOT to Add

- New vector DB for this milestone.
- Second LLM vendor for supervisor unless GigaChat routing proves inadequate.
