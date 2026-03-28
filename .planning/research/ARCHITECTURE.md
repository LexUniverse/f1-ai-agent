# Architecture Research

**Domain:** LangGraph supervisor replacing live F1 API with Tavily  
**Researched:** 2026-03-27  
**Confidence:** HIGH

## Integration with Existing Architecture

**Current:** FastAPI `chat.py` → retrieve → optional live (f1api) → `gigachat_rag` / template.

**Target:**

1. **Supervisor node (GigaChat):** Parse user message + session context; optional parallel **classify** / **plan** (lightweight).
2. **RAG node:** Existing retriever + chunk assembly; output `EvidenceBundle` + sufficiency metadata.
3. **Sufficiency gate:** If sufficient → **answer node** (GigaChat consumes evidence only).
4. **Tool node:** If insufficient → build Tavily query (GigaChat) → `TavilySearch` (LangChain) → **answer node** with web + optional RAG merge.
5. **Answer node:** Unified structured RU payload matching Pydantic models; map citations to numbered sources (RAG doc ids + URLs).

## New vs Modified Components

| Component | Action |
|-----------|--------|
| `src/integrations/f1api_client.py` | Remove or isolate behind feature flag removed in v1.2 |
| `src/api/chat.py` | Wire LangGraph runner instead of inline branch |
| New `src/graph/` or `src/agent/` | Graph definition, state schema, nodes |
| `gigachat_rag.py` | Possibly split: “evidence-only” vs “evidence + web” prompts |

## Data Flow

```text
User → Supervisor → RAG → [sufficient?] → synthesize
                    ↘ [not sufficient] → Tavily tool → synthesize
```

## Suggested Build Order

1. State schema + graph skeleton + mock Tavily.
2. Sufficiency gate + logging.
3. Real Tavily + LangChain tool.
4. Remove f1api dependency from live path; update `details` schema (replace `live` with `web` or generalize `external`).
5. README + env tests.

## Async FastAPI

- Run graph in threadpool or `asyncio.to_thread` if LangGraph sync; avoid blocking event loop.
