# Pitfalls Research

**Domain:** Multilingual Formula 1 assistant (RAG + live API + anti-hallucination)
**Researched:** 2026-03-26
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: Retrieval language mismatch (RU query, EN corpus) silently degrades grounding

**What goes wrong:**
Users ask in Russian, but most F1 source text is English. Retrieval misses key context, then the model answers from priors and sounds confident but wrong.

**Why it happens:**
Teams assume a single embedding model is "multilingual enough" without testing RU->EN retrieval recall on domain terms (team names, old sponsor names, transliterations).

**How to avoid:**
Use cross-lingual retrieval explicitly (multilingual embeddings + reranking), normalize motorsport entities (aliases/transliterations), and evaluate retrieval by language pair (RU->EN, RU->RU, EN->EN) before launch.

**Warning signs:**
- Good answers in English test prompts, weak answers for equivalent Russian prompts.
- Correct citations format but weak evidence relevance.
- Frequent fallback to generic F1 background paragraphs for specific historical questions.

**Phase to address:**
Phase 2 - Retrieval foundation and multilingual evaluation harness.

---

### Pitfall 2: RAG-first policy is implemented as prompt text, not enforced in control flow

**What goes wrong:**
Assistant claims "RAG-first" but actually skips retrieval in edge cases or uses stale retrieved context when live data is required (next race, latest result).

**Why it happens:**
Policy is left to LLM instruction following instead of deterministic routing logic in the graph.

**How to avoid:**
Implement hard routing contracts in LangGraph: (1) retrieve first, (2) run sufficiency check, (3) call live API only when evidence is insufficient or freshness threshold fails, (4) emit provenance flags in response schema.

**Warning signs:**
- Same question alternates between retrieved and non-retrieved behavior.
- No machine-readable trace showing whether retrieval and API checks ran.
- "Current season" answers cite static historical chunks.

**Phase to address:**
Phase 3 - Orchestration policies and deterministic tool-routing contracts.

---

### Pitfall 3: No freshness contract between historical DB and live API

**What goes wrong:**
Assistant mixes historical and live records without temporal reconciliation (timezone, race weekend state, post-race corrections), creating contradictory answers.

**Why it happens:**
RAG chunks and API responses are merged ad hoc with no data validity window, no "as-of" timestamp semantics, and no conflict resolution rule.

**How to avoid:**
Define canonical time semantics: every answer carries `as_of`, source timestamps, and conflict precedence rules (live > cached > static, with exceptions). Build merge logic as code, not prose in prompts.

**Warning signs:**
- Different answers to identical question within minutes.
- Contradictions between cited historical context and claimed "latest" standing/result.
- User reports "race already finished" while assistant still reports "upcoming."

**Phase to address:**
Phase 4 - Data contracts and temporal consistency layer.

---

### Pitfall 4: Citation plumbing exists, but faithfulness is not actually verified

**What goes wrong:**
Responses include citations, but claims are not supported by cited spans (citation theater). This fails anti-hallucination goals while appearing compliant.

**Why it happens:**
Teams implement citation formatting only, without automated citation-to-claim support checks and abstention rules when support is missing.

**How to avoid:**
Treat citations as verifiable outputs: require stable source IDs, validate support for each key claim, fail closed when evidence is absent, and add "cannot verify from sources" response mode.

**Warning signs:**
- Cited chunks mention adjacent topics, not the exact asserted fact.
- High answer fluency despite low retrieval confidence scores.
- Low disagreement between model and evaluator because both use same weak context.

**Phase to address:**
Phase 5 - Grounded response schema, citation validation, and abstention behavior.

---

### Pitfall 5: LangGraph state misuse causes memory loss or runaway loops

**What goes wrong:**
Conversation context disappears between turns, or the agent loops across planner/tool/evaluator nodes until recursion limits or cost alarms hit.

**Why it happens:**
Missing reducers for message channels, weak termination criteria, no proactive recursion handling, or missing `thread_id`/checkpointer configuration.

**How to avoid:**
Use `add_messages`-style message reducers, persistent checkpointers with explicit `thread_id`, bounded loop criteria, and proactive remaining-step routing to graceful fallback.

**Warning signs:**
- Assistant "forgets" prior turns in same session.
- GraphRecursion errors in logs or sudden long-tail latency.
- Repeated tool calls with near-identical inputs.

**Phase to address:**
Phase 3 - Graph runtime hardening (state, persistence, loop controls).

---

### Pitfall 6: F1 entity normalization is skipped (drivers/teams/circuits across eras)

**What goes wrong:**
The assistant fails to join evidence for the same entity across naming variants (e.g., team rebrands, transliterations, historical constructors), producing incomplete or wrong historical answers.

**Why it happens:**
Raw source strings are treated as canonical IDs; no alias map for Russian/English and no era-aware entity model.

**How to avoid:**
Create canonical entity registry (driver/team/circuit IDs) with alias tables (RU, EN, historical names), and resolve mentions before retrieval and before output generation.

**Warning signs:**
- Correct facts for modern seasons but degraded accuracy in historical queries.
- Duplicate entities in retrieved context that should be one canonical subject.
- User phrasing variant drastically changes answer quality.

**Phase to address:**
Phase 2 - Domain data modeling and entity normalization.

---

### Pitfall 7: Degraded mode is announced inconsistently or too late

**What goes wrong:**
When live API is unavailable, assistant still returns high-confidence statements or only notes outage after giving potentially stale claims.

**Why it happens:**
Error handling is not part of response contract; degraded-mode status is side-channel logging, not enforced output behavior.

**How to avoid:**
Make degraded mode a first-class output field (`mode=degraded`, confidence caps, user-visible caveat), and require fallback behavior per question type (historical-only vs live-dependent).

**Warning signs:**
- Infra logs show API failures while user-visible responses omit uncertainty.
- Confidence language unchanged between healthy and outage periods.
- No alerting on proportion of degraded responses.

**Phase to address:**
Phase 6 - Reliability, outage handling, and user trust messaging.

---

### Pitfall 8: Evaluation set is broad but not adversarial for hallucination failure modes

**What goes wrong:**
Model appears to meet target accuracy in curated tests but fails on real user traffic (ambiguous phrasing, mixed RU/EN, trick historical comparisons, stale live context).

**Why it happens:**
Teams optimize for average-case QA, not hard negative and edge-case slices that trigger hallucinations.

**How to avoid:**
Build a stratified eval suite: multilingual parity tests, no-answer-required tests, temporal consistency tests, citation-faithfulness tests, and regression gates before deployment.

**Warning signs:**
- Offline metrics high, but production corrections rise.
- Failures cluster in long-tail historical or bilingual prompts.
- No per-slice accuracy reporting by language/time-sensitivity/question type.

**Phase to address:**
Phase 5 - Anti-hallucination eval framework and release gates.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single-vector-store without metadata filters | Fast MVP | Cannot enforce season/source/freshness constraints; hallucination risk rises | Only for prototype before Phase 2 |
| Prompt-only tool policy ("use API if needed") | Less engineering upfront | Non-deterministic behavior, policy drift | Never for production |
| Using in-memory checkpointer in production | Easy setup | Lost conversational memory on restarts | Never |
| No entity alias registry | Faster ingestion | Historical and RU query accuracy collapses | Never beyond internal demo |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Live F1 API (`f1api.dev`) | Assuming enterprise SLA/rate-limit behavior without explicit contract | Wrap with retries, timeout budgets, circuit breaker, caching TTLs, and degraded-mode fallbacks |
| Vector DB + embeddings | Re-embedding incrementally without version tagging | Track embedding model/version per chunk; run backfill migrations intentionally |
| LangGraph + storage | Missing persistent checkpointer or `thread_id` | Enforce thread-aware invocation contract and persistent saver |
| Auth allowlist | Relying on frontend-only checks | Validate user code server-side for every request and audit access events |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Always-hit live API for "current" intents | Latency spikes and quota exhaustion | Freshness cache by endpoint + schedule + invalidation policy | Usually visible by 100-300 DAU |
| Large chunk retrieval without reranking | Long contexts, weak grounding precision | Smaller semantically coherent chunks + reranker + top-k budgets | Degrades once corpus reaches multi-season depth |
| Synchronous external calls inside graph path | Tail latency and timeouts | Async I/O, bounded concurrency, and per-node timeout policies | Under moderate concurrent chat sessions |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Treating allowlist code as identity only (no rotation or audit) | Unauthorized sharing and silent abuse | Rotating codes, per-code usage analytics, and revocation flow |
| Logging full prompts/tool payloads with user identifiers | Privacy leakage and compliance risk | Redact identifiers and separate operational logs from content logs |
| Unvalidated tool parameters from LLM | Tool abuse, malformed upstream requests | Schema-validate tool calls and constrain allowed parameter ranges |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Mixing certainty tone with uncertain evidence | Users trust wrong answers | Confidence-calibrated language tied to evidence quality |
| Translating technical motorsport terms too aggressively | Loss of factual nuance in RU | Preserve canonical term + localized explanation |
| Hiding source freshness | Users cannot judge reliability for live questions | Show `as_of` timestamp and source type in answer footer |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **RAG pipeline:** Often missing retrieval quality eval by language pair — verify RU->EN recall and faithfulness slices.
- [ ] **Live API integration:** Often missing outage simulation — verify degraded-mode user messaging and confidence cap.
- [ ] **Citations:** Often missing support validation — verify claims are directly backed by cited chunks.
- [ ] **LangGraph orchestration:** Often missing loop termination tests — verify no runaway routes under ambiguous prompts.
- [ ] **Entity model:** Often missing historical alias coverage — verify cross-era team/driver normalization.

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Retrieval language mismatch | MEDIUM | Add bilingual eval set, retrain/reconfigure embeddings, introduce reranker, reindex corpus |
| Citation theater / unsupported claims | HIGH | Activate strict abstention, ship citation validator, rollback risky prompt variants |
| Temporal inconsistency with live data | HIGH | Freeze live-dependent intents to degraded mode, patch merge policy, replay recent answers for audit |
| LangGraph loop/runaway costs | MEDIUM | Lower recursion budget, add RemainingSteps routing, enforce stop conditions, redeploy |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Retrieval language mismatch | Phase 2 | RU/EN retrieval parity benchmark passes threshold |
| RAG policy not enforced in flow | Phase 3 | Traces show deterministic retrieve->sufficiency->API routing |
| No freshness contract | Phase 4 | Every live-dependent response includes valid `as_of` and source timestamps |
| Citation theater | Phase 5 | Automated claim-support checks block unsupported outputs |
| LangGraph memory/loop failures | Phase 3 | Multi-turn thread retention and recursion stress tests pass |
| Entity normalization gaps | Phase 2 | Alias resolution tests across eras and RU/EN variants pass |
| Weak degraded mode behavior | Phase 6 | Chaos tests prove explicit degraded responses during API failure |
| Non-adversarial evals | Phase 5 | Release gate includes adversarial multilingual + temporal slices |

## Sources

- LangGraph Graph API (state, reducers, recursion, control flow): https://docs.langchain.com/oss/python/langgraph/graph-api (HIGH)
- LangGraph Persistence (threads/checkpointers/fault tolerance): https://docs.langchain.com/oss/python/langgraph/persistence (HIGH)
- OpenAI Reasoning best practices (planner/doer patterns, reliability): https://developers.openai.com/api/docs/guides/reasoning-best-practices/ (HIGH)
- OpenAI Citation formatting guide (citable units, validation plumbing): https://developers.openai.com/api/docs/guides/citation-formatting (HIGH)
- F1 API docs (`f1api.dev`) for endpoint surface and live-data integration context: https://f1api.dev/docs (MEDIUM)
- Cross-lingual RAG challenge references (ecosystem signal, needs local validation): https://www.aclanthology.org/2025.findings-emnlp.849/ (MEDIUM)

---
*Pitfalls research for: Formula 1 multilingual assistant*
*Researched: 2026-03-26*
