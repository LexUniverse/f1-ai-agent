# Phase 8 — Technical Research: LangGraph + Tavily + f1api removal

**Phase:** 8 — LangGraph Supervisor & Tavily Tooling  
**Date:** 2026-03-28  
**Requirement IDs:** AGT-01, AGT-02, SRCH-01, SRCH-02

## RESEARCH COMPLETE

## Executive summary

Replace the monolithic `src/api/chat.py` branch tree with a **compiled LangGraph** run **synchronously** inside **`asyncio.to_thread`** from an **`async def`** `/next_message` handler (per **08-CONTEXT D-08**). Use **LangChain Community**’s **Tavily** tool wrapper (**one call per turn**, **D-03**) with env-driven **`TAVILY_API_KEY`** and timeout. **RAG sufficiency** is **hybrid** (**D-01–D-02**): deterministic pass/fail on empty evidence and strong scores; **GigaChat JSON judge** only when the **top Chroma score** falls in a **documented band** adjacent to `min_score` (today **0.35** in `chat.py` / `retriever.py`). On Tavily failure: **`WEB_SEARCH_UNAVAILABLE`** + fixed RU message (**D-04**). **URLs** land in **`structured_answer.sources_block_ru`** only until Phase 9 (**D-05**). Remove **`F1ApiClient`**, **`gigachat_synthesize_f1api_context`**, and live fetch branches (**D-06**).

## Stack choices

| Package | Role | Notes |
|---------|------|--------|
| `langgraph` | `StateGraph`, `START`/`END`, conditional edges | Prefer **0.2.x** line compatible with Python 3.11+; use **sync** `invoke` inside thread. |
| `langchain-core` | Messages/tool abstractions if needed | Align minor with `langcommunity`. |
| `langchain-community` | `TavilySearchResults` or `TavilySearchAPIWrapper` | Single search per turn; read API key from env. |

**Pin strategy:** Add upper bounds in `requirements.txt` to match current ecosystem (e.g. `langgraph>=0.2,<0.3`, `langchain-core>=0.3,<0.4`, `langchain-community>=0.3,<0.4`) and run `pip install` once to resolve; adjust if resolver conflicts.

## Graph topology (AGT-01)

Explicit nodes (names illustrative):

1. **`ingest`** — Normalize inputs: `user_question`, optional precomputed `normalized_query` / entity ids from existing `resolve_entities` (keep outside graph per **08-CONTEXT** discretion to minimize session churn).
2. **`retrieve`** — Call `retrieve_historical_context` + `format_evidence` (same params as today: `top_k=5`, `min_score=0.35`).
3. **`sufficiency`** — Compute `top_score` from raw hits if needed; apply **rules**; optionally call **`gigachat_judge_sufficiency`** (new thin helper in `gigachat_rag` or `src/graph/judge.py`) returning boolean JSON.
4. **`branch`** — Conditional: sufficient → **`synthesize_rag`**; else → **`tavily_search`**.
5. **`tavily_search`** — Build search query via **GigaChat** (single short completion) or deterministic fallback from user question; invoke Tavily **once**; populate `web_snippets` + `web_urls` list in state.
6. **`synthesize_rag`** — Existing `gigachat_synthesize_historical` + template fallback pattern.
7. **`synthesize_web`** — New **`gigachat_synthesize_from_web_results`** (or equivalent): prompt lists **numbered web excerpts + URLs**; **`sources_block_ru`** must enumerate URLs per **SRCH-01** / **D-05**.
8. **`finalize`** — Assemble `details` dict + `message` + `status` for `NextMessageResponse`.

**Supervisor clarity:** Either a dedicated **`supervisor`** node that only routes, or **conditional edges** from `sufficiency` — both satisfy “explicit delegation” if **node names** and **graph diagram** in plan are clear.

## Sufficiency rules (AGT-02)

| Condition | Verdict |
|-----------|---------|
| `evidence` empty after format | **Insufficient** → Tavily path |
| `top_score >= SUFFICIENT_HIGH` (e.g. ≥ 0.45, TBD in impl) | **Sufficient** → RAG synthesis without judge |
| `SUFFICIENT_LOW ≤ top_score < SUFFICIENT_HIGH` (band around **0.35**) | Run **GigaChat judge**; if judge says insufficient → Tavily |
| Judge / GigaChat error on borderline | **Conservative:** treat as **insufficient** → Tavily (bounded cost) OR fail to template — **prefer Tavily attempt once** per product policy; document in code comment |

## Tavily integration (SRCH-01)

- **Query formulation:** Small GigaChat completion: “Produce one Russian or English web search query for Formula 1: …” — **one string**, no tool loop.
- **Timeout:** `float(os.environ.get("TAVILY_TIMEOUT", "10"))` parallel to Phase 5 live client spirit.
- **Results:** Map LangChain tool output to plain `{title, url, content}` dicts in state; cap **max document count** (e.g. 5) in prompt to control tokens.
- **Synthesis:** Grounding instruction: only cite URLs returned in state.

## f1api removal (SRCH-02)

- Delete **`src/integrations/f1api_client.py`** and **`tests/test_f1api_client.py`**.
- Remove **`app.state.f1_api_client`** from **`src/main.py`** and **`tests/conftest.py`**.
- Remove **`LiveUpstreamError`** imports from **`chat.py`**; remove branches using **`build_rag_fallback_context`**, **`fetch_current_next`**, **`gigachat_synthesize_live`** / **`gigachat_synthesize_f1api_context`** as wired today.
- **`requires_live_data`** (**`src/live/gate.py`**): reuse as **non-network “freshness intent”** signal inside sufficiency or Tavily query shaping **without** calling HTTP (per CONTEXT).
- **`LiveDetails`** / **`details.live`:** Phase 8 may stop emitting `live` for new answers; Streamlit Phase 7 still shows expander when key missing — **no Phase 9 work in this phase**. Historical path unchanged.

## FastAPI + async

- Change **`next_message`** to **`async def next_message`**.
- **`await asyncio.to_thread(run_f1_turn_sync, initial_state)`** where `run_f1_turn_sync` calls `graph.invoke`.
- **Starlette test client** supports async routes — update tests that use `client.post` (httpx **AsyncClient** or TestClient with async app — verify FastAPI `TestClient` compatibility with async endpoints: FastAPI wraps async; **TestClient** may need `with TestClient(app) as client` and sync post still works for single async route).

## Risks (from PITFALLS.md)

- **Event loop blocking** — mitigated by **to_thread**.
- **Flaky Tavily in CI** — all tests **mock** Tavily; no real network in default pytest.
- **Hallucinated URLs** — prompt + force `sources_block_ru` to list only provided URLs; conservative **confidence** for web-only path (e.g. `live_qna_confidence()` or dedicated tier).

## Validation Architecture

**Dimension 1 — Requirement traceability:** Each plan frontmatter lists AGT/SRCH IDs; tasks reference D-01…D-08 from `08-CONTEXT.md`.

**Dimension 2 — Test layering:** Unit tests for graph routing and sufficiency rules with **mocked** GigaChat/Tavily; API tests for `/next_message` with **monkeypatched** `run_f1_turn_sync` or graph.

**Dimension 3 — Contract preservation:** `NextMessageResponse` schema unchanged; new failure code **`WEB_SEARCH_UNAVAILABLE`** string exact match in tests.

**Dimension 4 — Degradation parity:** Failed web path mirrors `LIVE_UNAVAILABLE` payload shape (no `structured_answer` on failure).

**Dimension 5 — Security:** No secrets in repo; `TAVILY_API_KEY` from env only.

**Dimension 6 — Performance:** Single Tavily call; graph invoke in thread; timeouts documented.

**Dimension 7 — Observability:** `details.synthesis.route` extended with values e.g. `gigachat_rag`, `gigachat_web`, `template_fallback` (planner-defined constants).

**Dimension 8 — Nyquist / feedback loop:** After each task, `pytest` subset; full suite after wave 2.
