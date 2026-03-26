# Project Research Summary

**Project:** F1 Assistant (GigaChat + LangGraph)
**Domain:** RU-first asynchronous Formula 1 RAG assistant with conditional live data
**Researched:** 2026-03-26
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project is a reliability-first Formula 1 assistant: users ask in Russian, while the system grounds answers with historical F1 data plus selective live API augmentation. Strong implementations in this category use deterministic orchestration (not prompt-only autonomy), explicit provenance/citations, and a strict degraded-mode policy when live data is unavailable. The target product should optimize for trust: accurate, source-backed answers, consistent confidence signaling, and transparent freshness (`as_of`) semantics.

The recommended approach is FastAPI + LangGraph + ChromaDB with a supervisor-routed graph and typed contracts end-to-end. Default behavior should be RAG-first for historical/contextual questions, with live API calls only when freshness or insufficiency thresholds require them. Streamlit is the right v1 UI for shipping speed; architecture boundaries should keep graph logic, retrieval, integrations, and evaluation isolated so the system can harden without rewrites.

The highest risks are multilingual retrieval failure (RU queries over mostly EN corpora), citation theater (formatted citations without factual support), and temporal inconsistency between historical and live sources. Mitigation is known and concrete: multilingual retrieval eval slices, deterministic retrieve->sufficiency->live routing, citation-faithfulness validators, canonical entity normalization, and a first-class degraded response contract with confidence caps.

## Key Findings

### Recommended Stack

The stack recommendation is coherent and production-aligned for the project constraints: Python 3.12, FastAPI, LangGraph, ChromaDB, Streamlit, and GigaChat SDK with `langchain-gigachat`. This combination maximizes integration maturity while preserving rapid MVP delivery and later scaling paths.

Critical compatibility constraints are explicit and should be treated as pinned baselines: FastAPI with Pydantic v2, LangGraph 1.x with LangChain Core 1.x, and aligned GigaChat adapter/provider versions. The primary architecture risk is not framework choice but policy enforcement and evaluation discipline.

**Core technologies:**
- Python 3.12.x: runtime foundation — strongest ecosystem fit for async AI orchestration.
- FastAPI 0.135.2: API contracts and orchestration entrypoint — typed async endpoints with Pydantic validation.
- LangGraph 1.1.3: multi-step orchestration runtime — explicit state, routing, checkpoints, and policy controls.
- ChromaDB 1.5.5: vector + metadata retrieval — low-ops default for RAG MVP with filterable search.
- Streamlit 1.55.0: chat UI delivery — fastest path to operator/user-facing interface.
- GigaChat SDK 0.2.0 (+ `langchain-gigachat` 0.5.0): RU-centric model access with graph-native adapter support.

### Expected Features

The feature research is strongly aligned with project constraints: launch must prioritize trustworthy RU-first Q&A, historical grounding, conditional live augmentation, and explicit degraded mode. Advanced capabilities should be sequenced only after reliability baselines are demonstrated.

**Must have (table stakes):**
- Source-backed RU-first F1 Q&A for drivers/teams/races/standings with uncertainty handling.
- Historical RAG coverage with normalized stats/entities and citation-ready provenance.
- Live-session awareness via conditional API augmentation plus freshness timestamps.
- Core reminder utility (session alerts, optional non-spoiler mode).

**Should have (competitive):**
- Explainability mode with compact evidence cards and per-claim confidence.
- Dual-horizon answers (historical context + live implications).
- Strategy-aware insights (tyre/pit/DRS/race-control context) after live pipeline stability.
- Lightweight personal preference memory (team/driver/style) once baseline quality is stable.

**Defer (v2+):**
- Voice-first assistant.
- Heavy personalization/recommender systems.
- Social/community feed features.
- Multi-sport expansion.

### Architecture Approach

The recommended architecture is a supervisor-routed LangGraph pipeline behind FastAPI, with Streamlit as the client layer and Chroma + live API adapter in the data/integration layer. Major components should remain modular: API contracts (`app/api`), orchestration (`graph`), retrieval/indexing (`retrieval`), external tools/retries (`integrations`), and evaluation harness (`eval`). Key patterns are deterministic guardrails around agentic steps, two-tier knowledge access (RAG first, live second), and explicit state channels for confidence, freshness, citations, and degraded-mode behavior.

**Major components:**
1. Experience/API layer (Streamlit + FastAPI) — validate inputs, enforce auth, surface structured outputs.
2. Agent runtime (LangGraph supervisor + planner/retrieval/tool/evaluator/synthesizer) — route and enforce policy.
3. Data/integration layer (Chroma + f1api client + caching/circuit-breaker) — supply grounded historical and live facts.

### Critical Pitfalls

1. **RU->EN retrieval mismatch** — enforce multilingual embeddings/reranking, alias normalization, and RU/EN parity benchmarks.
2. **Prompt-only RAG policy drift** — implement deterministic retrieve->sufficiency->live control flow with traceable provenance flags.
3. **No temporal/freshness contract** — require `as_of`, source timestamps, and coded precedence rules for live vs cached vs static data.
4. **Citation theater** — validate claim-support links automatically; abstain when evidence is insufficient.
5. **LangGraph state/loop failures** — configure reducers + persistent checkpointer + bounded recursion + termination criteria.

## Implications for Roadmap

Based on dependencies and risk concentration, suggested phase structure:

### Phase 1: Platform Foundation and Trust Contracts
**Rationale:** Stable contracts, auth, and observability are prerequisites for reliable agent behavior and auditing.  
**Delivers:** FastAPI skeleton, Pydantic schemas, allowlist auth, structured logging/tracing, response envelope (`answer`, `citations`, `confidence`, `mode`, `as_of`).  
**Addresses:** Access control, source-backed UX baseline.  
**Avoids:** Pitfall 2 (policy drift hidden by weak traces), Pitfall 7 (late/inconsistent degraded messaging).

### Phase 2: Retrieval Core and Multilingual Data Modeling
**Rationale:** Core product value is grounded RU-first Q&A; retrieval correctness must precede advanced orchestration.  
**Delivers:** f1db ingestion, Chroma index, metadata filters, canonical entity registry (RU/EN aliases, historical names), RU/EN retrieval parity eval slice.  
**Uses:** ChromaDB, multilingual retrieval tooling, Pydantic contracts.  
**Implements:** `retrieval/` module and citations normalization boundary.  
**Avoids:** Pitfall 1 (language mismatch), Pitfall 6 (entity normalization gaps).

### Phase 3: Supervisor Orchestration and Deterministic Routing
**Rationale:** Once retrieval baseline exists, move to controlled multi-agent routing for consistent behavior under mixed intents.  
**Delivers:** LangGraph state schema, supervisor + planner + evaluator nodes, deterministic retrieve->sufficiency->route logic, persistent checkpointing/thread handling.  
**Addresses:** RAG-first enforcement and multi-turn consistency.  
**Avoids:** Pitfall 2 (prompt-only policies), Pitfall 5 (memory loss/runaway loops).

### Phase 4: Live Data Integration and Temporal Consistency
**Rationale:** Live augmentation is needed for current-session utility but should only arrive after deterministic routing.  
**Delivers:** Typed `f1api.dev` adapter, timeout/retry/circuit-breaker, TTL caching, freshness classifier, merge policy with timestamp precedence.  
**Addresses:** Live-session awareness and freshness requirements.  
**Avoids:** Pitfall 3 (historical/live contradictions), Pitfall 7 (unbounded confidence in outage conditions).

### Phase 5: Grounding QA and Anti-Hallucination Release Gates
**Rationale:** 98% accuracy and trust goals require formal validation before broad usage.  
**Delivers:** Citation-faithfulness checks, abstention mode, adversarial eval suite (bilingual, temporal, no-answer, long-tail historical), CI quality gates.  
**Addresses:** Explainability and trust signals for production hardening.  
**Avoids:** Pitfall 4 (citation theater), Pitfall 8 (non-adversarial eval blind spots).

### Phase 6: UX Reliability and Differentiator Expansion
**Rationale:** Add differentiators only after reliability, grounding, and live consistency are stable.  
**Delivers:** Session reminders/non-spoiler polish, race companion enhancements, strategy insights, optional lightweight memory layer.  
**Addresses:** P2 differentiators from feature research.  
**Avoids:** Premature complexity from voice/social/deep personalization anti-features.

### Phase Ordering Rationale

- Dependency-first: trust contract -> retrieval correctness -> orchestration control -> live integration -> release gates -> advanced UX.
- Architecture-aligned grouping: boundaries mirror `app`, `graph`, `retrieval`, `integrations`, `eval`, and UI presenter modules.
- Risk burn-down ordering: highest hallucination and inconsistency risks are mitigated before feature expansion.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2:** multilingual retrieval model/reranker choice and RU motorsport entity normalization strategy.
- **Phase 4:** `f1api.dev` reliability envelope, rate limits, and robust freshness conflict resolution under race-weekend volatility.
- **Phase 5:** citation-faithfulness validation design and adversarial eval dataset construction for bilingual temporal QA.

Phases with standard patterns (can likely skip `/gsd-research-phase`):
- **Phase 1:** FastAPI + Pydantic + auth dependency + observability setup are well-documented.
- **Phase 3:** LangGraph supervisor/state/checkpointer patterns are well-covered by official docs.
- **Phase 6 (core reminder UX only):** standard product/notification patterns with low technical uncertainty.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Version-pinned recommendations with strong official docs and explicit compatibility mapping. |
| Features | MEDIUM | Strong market signals and official ecosystem references; some assumptions still need RU-user validation. |
| Architecture | HIGH | Supervisor/state/contract patterns are mature and well-documented; clear modular boundaries. |
| Pitfalls | MEDIUM-HIGH | Failure modes are realistic and actionable, but some mitigation thresholds require project-specific calibration. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **RU user behavior validation:** confirm top intents, acceptable latency tradeoffs, and non-spoiler expectations via early UAT.
- **Live API operational envelope:** validate race-day rate limits, outage patterns, and stale-data windows with synthetic load tests.
- **Multilingual retrieval benchmark thresholds:** define pass/fail targets for RU->EN recall, rerank precision, and citation support rates.
- **Accuracy metric contract:** formalize exact rubric for the 98% target (question slices, scoring rules, abstention handling).

## Sources

### Primary (HIGH confidence)
- [FastAPI docs](https://fastapi.tiangolo.com/) — async patterns, project structure, validation contracts.
- [LangGraph docs](https://docs.langchain.com/oss/python/langgraph/graph-api) — state graph model, routing, reducers, recursion control.
- [LangGraph persistence docs](https://docs.langchain.com/oss/python/langgraph/persistence) — thread/checkpointer behavior.
- [LangGraph supervisor references](https://reference.langchain.com/python/langgraph-supervisor/) — supervisor routing patterns.
- [Pydantic docs](https://docs.pydantic.dev/latest/concepts/models/) — schema modeling and validation.
- [Streamlit architecture docs](https://docs.streamlit.io/develop/concepts/architecture/architecture) — session and client-server behavior.
- [F1DB README](https://raw.githubusercontent.com/f1db/f1db/main/README.md) — historical data coverage.
- [Jolpica F1 API README](https://raw.githubusercontent.com/jolpica/jolpica-f1/main/docs/README.md) — endpoint/data surface.

### Secondary (MEDIUM confidence)
- [Chroma docs](https://docs.trychroma.com/docs/overview/introduction) — retrieval capabilities and operational patterns.
- [f1api.dev docs](https://f1api.dev/docs) — live endpoint integration context.
- [Formula1.com app announcement](https://www.formula1.com/en/latest/article/never-miss-a-moment-with-the-official-f1-app.4VryQGIJyCKZJp2eSNj4L5) — feature baseline expectations.
- [Formula1.com app relaunch](https://www.formula1.com/en/latest/article/formula-1-launches-new-website-and-personalised-mobile-app.1knZbPSCZ2tS2z6ADRn2Gs) — personalization and product direction.
- [Formula1.com Apple integration](https://www.formula1.com/en/latest/article/apple-reveal-details-of-f1-integration-on-apple-tv-apple-maps-apple-news-and.4JJY1CUT4eobqZ78wTcO3L) — telemetry/live companion context.
- [Official F1 App listing](https://apps.apple.com/gb/app/official-f1-app/id835022598) — practical feature snapshot.

### Tertiary (LOW confidence / validate locally)
- [Cross-lingual RAG challenge reference](https://www.aclanthology.org/2025.findings-emnlp.849/) — ecosystem signal for multilingual retrieval risk patterns.
- [OpenAI citation/reasoning best-practice guides](https://developers.openai.com/api/docs/guides/citation-formatting) — generic implementation guidance, not domain-specific constraints.

---
*Research completed: 2026-03-26*
*Ready for roadmap: yes*
