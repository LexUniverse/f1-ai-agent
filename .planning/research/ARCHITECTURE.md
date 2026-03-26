# Architecture Research

**Domain:** Supervisor-routed multi-agent RAG + live API Formula 1 assistant
**Researched:** 2026-03-26
**Confidence:** MEDIUM-HIGH

## Standard Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                            Experience Layer                                  │
├───────────────────────────────────────────────────────────────────────────────┤
│  Streamlit Chat UI  │  Auth Code Gate  │  Session State  │  Response Viewer │
└───────────────┬──────────────────────────────┬───────────────────────────────┘
                │                              │
┌───────────────┴──────────────────────────────┴───────────────────────────────┐
│                             API Layer (FastAPI)                              │
├───────────────────────────────────────────────────────────────────────────────┤
│  /chat endpoint  │  Request validator  │  Orchestration service             │
└───────────────┬──────────────────────────────┬───────────────────────────────┘
                │ invokes graph                │ metrics/logs
┌───────────────┴──────────────────────────────┴───────────────────────────────┐
│                   Agent Runtime Layer (LangGraph StateGraph)                 │
├───────────────────────────────────────────────────────────────────────────────┤
│ Supervisor Router -> Planner -> Retrieval Agent -> Tool Agent -> Evaluator   │
│       │                │            │                │              │         │
│       └────────────── state + policy + provenance channels ─────────┘         │
└───────────────┬──────────────────────────────┬───────────────────────────────┘
                │                              │
┌───────────────┴──────────────────────────────┴───────────────────────────────┐
│                              Data Layer                                       │
├───────────────────────────────────────────────────────────────────────────────┤
│ Chroma (f1db embeddings) │ Metadata cache │ Live API adapter (f1api.dev)     │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| `streamlit_app` | Collect user prompt, show grounded answer + degraded-mode notices | Streamlit chat, `st.session_state`, websocket session |
| `auth_gateway` | Enforce per-user allowlist code before any graph invocation | FastAPI dependency + short-lived session token |
| `chat_api` | Validate request/response contracts and call orchestration service | FastAPI async route + Pydantic models |
| `orchestrator` | Build graph input, invoke graph, map graph output to API response | Service module wrapping LangGraph compiled app |
| `supervisor` | Route turn to the right worker (RAG/tool/synthesize) and stop conditions | LangGraph supervisor pattern (`create_supervisor`) |
| `planner_node` | Convert user intent into retrieval/tool plan and confidence target | Deterministic node + optional LLM planning |
| `retrieval_agent` | Retrieve, filter, rerank F1 historical context and citations | Chroma retriever + metadata filters + reranker |
| `tool_agent` | Fetch live race/driver/standings data when planner marks freshness required | Typed API client with timeout/retry/circuit breaker |
| `evaluator_node` | Verify evidence sufficiency, enforce no-hallucination/degraded policy | Rule checks + lightweight LLM judge with thresholds |
| `response_synthesizer` | Produce RU-first structured answer with citations and confidence | LLM node constrained by response schema |
| `observability` | Traces, latency metrics, failure classification, replay for QA | LangSmith/OpenTelemetry + structured logs |

## Recommended Project Structure

```
src/
├── app/                         # FastAPI surface and composition root
│   ├── main.py                  # app startup, DI wiring
│   ├── api/chat.py              # /chat endpoint
│   └── api/schemas.py           # Pydantic request/response contracts
├── graph/                       # LangGraph runtime and nodes
│   ├── state.py                 # TypedDict/Pydantic graph state channels
│   ├── supervisor.py            # supervisor construction and routing policy
│   ├── nodes/                   # planner/retrieval/tool/evaluator/synthesizer
│   └── policies/                # confidence thresholds, fallback rules
├── retrieval/                   # RAG indexing and query path
│   ├── ingest_f1db.py           # ingestion/chunking/embedding pipeline
│   ├── retriever.py             # query + metadata filter + rerank
│   └── citations.py             # provenance normalization
├── integrations/                # external systems
│   ├── f1api_client.py          # live API adapter
│   ├── circuit_breaker.py       # retry/timeout/open-closed states
│   └── cache.py                 # short TTL read cache
├── ui/                          # Streamlit frontend
│   ├── app.py                   # chat UX
│   └── presenters.py            # render answer/citations/degraded status
├── eval/                        # offline accuracy + regression harness
│   ├── datasets/                # validation prompts and expected facts
│   └── runner.py                # scoring pipeline
└── shared/
    ├── config.py                # env-driven settings
    └── logging.py               # structured logging setup
```

### Structure Rationale

- **`graph/` separated from `app/`:** keeps orchestration logic testable without HTTP or UI concerns.
- **`retrieval/` isolated:** ingestion and query runtime evolve at different speeds and should not couple to API adapters.
- **`integrations/` boundary:** live API failures, retries, and auth stay outside agent prompts/nodes.
- **`eval/` as first-class module:** accuracy target (98%) requires repeatable regression checks, not ad hoc scripts.

## Architectural Patterns

### Pattern 1: Supervisor + Specialized Workers (Recommended Core)

**What:** A central supervisor routes tasks to specialized nodes/agents (planner, retriever, live tool, evaluator, synthesizer).
**When to use:** Multi-step QA where some requests need only RAG while others need fresh API data.
**Trade-offs:** Better control/observability than single-agent tool use, but requires careful state schema and routing policies.

**Example:**
```python
# Simplified routing intent in graph state
if state["needs_live_data"]:
    return "tool_agent"
if state["retrieval_confidence"] < state["min_confidence"]:
    return "retrieval_agent"
return "response_synthesizer"
```

### Pattern 2: Deterministic Guardrails Around Agentic Steps

**What:** Keep sensitive decisions deterministic (auth, degraded-mode messaging, timeout budgets, schema validation), while using LLMs for language and semantic reasoning.
**When to use:** Accuracy-sensitive assistants where hallucinations and silent failures are unacceptable.
**Trade-offs:** Slightly more boilerplate, but much more predictable behavior and easier incident debugging.

**Example:**
```python
if api_status == "unavailable":
    state["degraded_mode"] = True
    state["uncertainty_note"] = "Live API unavailable; answer based on historical corpus."
```

### Pattern 3: Two-Tier Knowledge Access (RAG First, Live API Second)

**What:** Default to vector retrieval for historical facts, then call live API only when freshness is required or retrieval confidence is below threshold.
**When to use:** Domains with mostly stable history plus periodic real-time updates (F1 race weekends).
**Trade-offs:** Lower cost/latency for most queries; requires robust freshness classifier to avoid unnecessary live calls.

## Data Flow

### Request Flow

```
User (RU prompt)
  ↓
Streamlit UI (auth code + session)
  ↓
FastAPI /chat (Pydantic validation)
  ↓
Orchestrator builds GraphState
  ↓
Supervisor routes:
  planner -> retrieval_agent -> (optional) tool_agent -> evaluator -> synthesizer
  ↓
Response contract: answer + citations + confidence + degraded_mode
  ↓
UI renders structured response and source cards
```

### State Management

```
GraphState channels:
messages, user_intent, retrieval_hits, live_api_payload,
retrieval_confidence, needs_live_data, degraded_mode, citations

Node update model:
Node reads subset -> emits partial update -> reducers merge into state
```

### Key Data Flows

1. **Historical answer flow:** Prompt -> planner marks `needs_live_data=false` -> retrieval + rerank -> evaluator passes -> synthesize with citations.
2. **Live weekend flow:** Prompt implies current standings/results -> planner marks `needs_live_data=true` -> live API fetch -> merge with retrieved background context -> synthesize with freshness note.
3. **Degraded flow:** Live API timeout/failure -> circuit breaker opens -> evaluator enforces degraded disclaimer -> synthesize conservative answer with explicit uncertainty.

## Suggested Build Order (Roadmap Implications)

1. **Foundation: contracts + observability + auth**
   - Build FastAPI skeleton, Pydantic schemas, allowlist auth, request tracing.
   - Rationale: everything else depends on stable contracts and secure entrypoint.
2. **RAG baseline path (single-agent or minimal graph)**
   - Ingest f1db into Chroma, implement retrieval + citations, return grounded answers.
   - Rationale: proves core value quickly and creates baseline metrics.
3. **Introduce LangGraph state + supervisor routing**
   - Add explicit state channels, planner, supervisor routing, evaluator node.
   - Rationale: convert linear pipeline to controllable multi-agent runtime.
4. **Add live API adapter + fallback policy**
   - Implement f1api client, timeout/retry/circuit breaker, degraded-mode behavior.
   - Rationale: freshness features without sacrificing reliability.
5. **Hardening and quality gates**
   - Add evaluation harness, regression dataset, latency/accuracy SLO checks, Docker deployment.
   - Rationale: needed to sustain 98% accuracy and <=10s response target.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | Single FastAPI + Streamlit deployment, in-process graph runtime, Chroma local/persistent volume |
| 1k-100k users | Split UI/backend, managed vector store, Redis cache, async worker pool for graph/tool calls |
| 100k+ users | Separate orchestration service, queue-based workload smoothing, read replicas/cached snapshots for high-demand race events |

### Scaling Priorities

1. **First bottleneck:** retrieval latency under concurrent load; fix with caching, index tuning, and metadata-pruned search.
2. **Second bottleneck:** live API rate limits/outages on race days; fix with TTL caches, circuit breaker, and stale-while-revalidate.

## Anti-Patterns

### Anti-Pattern 1: Pure Agentic Autonomy for Critical Routing

**What people do:** Let one LLM decide everything (whether to call APIs, confidence, and final answer policy).
**Why it's wrong:** Routing becomes non-deterministic and hard to debug; degraded mode can be skipped.
**Do this instead:** Keep routing gates and fallback policy deterministic; use LLMs for semantic subtasks only.

### Anti-Pattern 2: Treating Live API as Primary Knowledge Source

**What people do:** Hit live endpoints for most questions, including historical context.
**Why it's wrong:** Adds latency/cost and failure surface for data already in corpus.
**Do this instead:** RAG-first policy with explicit freshness triggers for live calls.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| `f1api.dev` | Async typed client with timeout/retry/circuit breaker | Map API failures to explicit degraded-mode state |
| LLM provider(s) | LangChain model interface with provider abstraction | Keep model configurable for fallback/provider swap |
| Chroma | Retriever abstraction in `retrieval/` | Keep vector index details out of graph logic |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `api` ↔ `graph` | Typed DTO + function call | No direct HTTP concerns inside graph nodes |
| `graph` ↔ `retrieval` | Interface (`search(query, filters)`) | Enables retriever changes without routing rewrites |
| `graph` ↔ `integrations` | Tool adapter methods | Central place for retries, limits, and error mapping |

## Sources

- LangGraph multi-agent tutorial: https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/ (HIGH)
- LangGraph Graph API concepts (state/nodes/edges/reducers): https://docs.langchain.com/oss/python/langgraph/graph-api (HIGH; retrieved via langgraph docs mirror)
- LangGraph Supervisor package reference: https://reference.langchain.com/python/langgraph-supervisor/ (HIGH)
- FastAPI async model: https://fastapi.tiangolo.com/async/ (HIGH)
- FastAPI bigger applications structure: https://fastapi.tiangolo.com/tutorial/bigger-applications/ (HIGH)
- Pydantic models and validation: https://docs.pydantic.dev/latest/concepts/models/ (HIGH)
- Streamlit client-server architecture/session constraints: https://docs.streamlit.io/develop/concepts/architecture/architecture (HIGH)
- Chroma overview (retrieval capabilities): https://docs.trychroma.com/docs/overview/introduction (MEDIUM; overview-level source)

---
*Architecture research for: Formula 1 assistant (supervisor-routed multi-agent RAG + live API)*
*Researched: 2026-03-26*
