# Phase 3: Historical RAG Grounding - Research

**Researched:** 2026-03-27
**Domain:** Historical RAG over f1db + multilingual alias resolution (RU/EN) + traceable evidence synthesis
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Retrieval Pipeline Shape
- **D-01:** Retrieval executes inline in `/next_message` during Phase 3 (no queue/service split yet).
- **D-02:** Retrieval output is a required intermediate artifact before final answer synthesis.

### RU/EN Entity Alias Strategy
- **D-03:** Use a canonical RU/EN alias dictionary with normalized matching (dictionary-first).
- **D-04:** Phase 3 does not use fuzzy-first entity matching to avoid low-trust false positives.

### Traceability Output Contract
- **D-05:** Return top-k evidence items that include source ID, short snippet, entity tags, and rank score.
- **D-06:** Evidence records must be explicitly tied to final answer synthesis to satisfy traceability requirements.

### Historical Indexing Boundary
- **D-07:** Phase 3 indexes historical `f1db` snapshot data only.
- **D-08:** Phase 3 does not call live APIs; live enrichment and freshness logic are deferred to Phase 5.

### Claude's Discretion
- Exact top-k default and score threshold values.
- Chunk sizing/token window strategy for retrieval snippets.
- Internal module boundaries for retriever, alias resolver, and evidence formatter.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

## Project Constraints (from .cursor/rules/)

No `.cursor/rules/` directory exists in this repository, so there are no additional project-specific rule constraints to enforce beyond phase context and requirements artifacts.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RAG-01 | User can receive answers grounded in f1db historical data indexed in ChromaDB. | Use ChromaDB collection with metadata filters (`where`) and deterministic top-k retrieval in `/next_message`; include source IDs and snippets in response details. |
| RAG-02 | User queries are matched against RU/EN entity aliases (drivers, teams, races). | Implement dictionary-first canonical resolver with Unicode normalization + transliteration-safe alias tables before retrieval query construction. |
| RAG-03 | User receives traceable retrieved context references used for final answer synthesis. | Extend response contract with evidence array (`source_id`, `snippet`, `entity_tags`, `rank_score`) and require synthesis step to reference those evidence items explicitly. |
</phase_requirements>

## Summary

Phase 3 should be implemented as a deterministic, inline retrieval pipeline inside `POST /next_message`, preserving Phase 2's contract-first API behavior. The immediate objective is not broad agent orchestration; it is reliable historical grounding from indexed `f1db` content with explicit evidence provenance. This keeps behavior auditable and testable while satisfying trust-first product goals.

For multilingual retrieval quality, use a canonical entity layer before vector search. RU/EN aliases for drivers, teams, and races should be normalized to canonical IDs first, then used to enrich retrieval query text and metadata filters. This avoids fuzzy-first behavior and reduces false positives on transliterated or historical names.

Traceability must be first-class in API contracts. Retrieval output is a mandatory intermediate artifact, and final answer synthesis should cite exact evidence records returned by retriever logic. The planner should prioritize schema updates, deterministic retrieval flow, and targeted tests for RU/EN alias parity and evidence-to-answer linkage.

**Primary recommendation:** Build a small `retrieval/` boundary (alias resolver + retriever + evidence formatter) and wire it inline into `/next_message` with strict typed evidence output and pytest coverage for `RAG-01..03`.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `fastapi` | 0.135.2 | HTTP API surface and deterministic endpoint orchestration | Already used in codebase and current stable release; aligns with existing contract-first architecture |
| `pydantic` | 2.12.5 | Typed request/response models including evidence payloads | Already used and current stable line; strong schema enforcement for traceability contract |
| `chromadb` | 1.5.5 | Historical vector + metadata retrieval from indexed `f1db` corpus | Officially supports metadata filtering and retrieval primitives needed for deterministic grounding |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 9.0.2 | Requirement-level API/contract and retrieval behavior tests | Use for Wave 0 and per-task checks |
| `unicodedata` (stdlib) | Python stdlib | Unicode normalization for RU/EN alias matching | Always in alias normalization path |
| `difflib` (stdlib, optional fallback) | Python stdlib | Conservative suggestion hints for unmatched aliases | Only for non-authoritative "did you mean" diagnostics, not fuzzy-first retrieval |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `chromadb` | pgvector / Elasticsearch | Stronger ops/scaling options later, but unnecessary complexity for current inline Phase 3 scope |
| Pure alias dictionary | Full fuzzy/NER-first resolver | Better recall in noisy input but materially higher false-positive risk, contradicting D-04 trust constraint |

**Installation:**
```bash
pip install fastapi pydantic chromadb pytest
```

**Version verification (executed 2026-03-27):**
- `python3 -m pip index versions fastapi` -> latest `0.135.2` (installed: `0.135.2`)
- `python3 -m pip index versions pydantic` -> latest stable `2.12.5` (installed: `2.12.5`)
- `python3 -m pip index versions chromadb` -> latest `1.5.5` (installed status not detected in project env)

## Architecture Patterns

### Recommended Project Structure
```text
src/
├── retrieval/                 # Historical RAG implementation boundary
│   ├── alias_resolver.py      # RU/EN alias normalization -> canonical entities
│   ├── retriever.py           # Chroma query orchestration + filters + top-k
│   └── evidence.py            # Normalize retrieval hits into traceable contract
├── api/
│   └── chat.py                # Inline call path in /next_message
├── models/
│   └── api_contracts.py       # Add evidence-bearing response schema
└── sessions/
    └── store.py               # Keep state transitions deterministic on retrieval failures
```

### Pattern 1: Deterministic Inline Retrieve-Then-Synthesize
**What:** Execute retrieval in `/next_message`, capture top-k evidence, then synthesize answer from evidence only.  
**When to use:** All historical F1 queries in Phase 3.  
**Example:**
```python
# Source: project context + existing src/api/chat.py contract
canonical_query, entity_tags = alias_resolver.resolve(user_query)
hits = retriever.search(query=canonical_query, top_k=TOP_K, min_score=MIN_SCORE)
evidence = format_evidence(hits, entity_tags=entity_tags)
answer = synthesizer.from_evidence(user_query=user_query, evidence=evidence)
return NextMessageResponse(message=answer, status="ready", details={"evidence": evidence})
```

### Pattern 2: Alias Resolution Before Retrieval
**What:** Normalize input (Unicode + case + whitespace), then map RU/EN aliases to canonical entity IDs before vector search.  
**When to use:** Always, per D-03 and D-04.  
**Example:**
```python
# Source: phase decision D-03 dictionary-first
norm = normalize_text(query)  # NFC + lowercase + punctuation normalization
entities = canonical_alias_dict.match(norm)  # exact/normalized dictionary matching
retrieval_query = build_query_with_canonical_entities(query, entities)
```

### Pattern 3: Evidence-First Contract Extension
**What:** Add typed evidence records in response details and enforce answer-evidence linkage.  
**When to use:** All successful grounded responses in Phase 3.  
**Example:**
```python
class EvidenceItem(BaseModel):
    source_id: str
    snippet: str
    entity_tags: list[str]
    rank_score: float
```

### Anti-Patterns to Avoid
- **Fuzzy-first matching:** violates trust-first constraint and introduces silent alias drift.
- **Free-form citations:** citations that are not tied to retriever output fail RAG-03.
- **Retriever hidden in synthesis prompt only:** makes behavior non-deterministic and hard to test.
- **Unbounded chunk payloads:** oversized snippets degrade precision and increase hallucination pressure.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector indexing + similarity search | Custom in-memory cosine engine | `chromadb` collection/query APIs | Chroma already handles index/storage/query + metadata filters robustly |
| Data model validation | Ad hoc dict shape checks | Pydantic models in `src/models/api_contracts.py` | Prevents silent contract drift and improves deterministic error behavior |
| Complex transliteration engine | Heavy bespoke NLP pipeline in Phase 3 | Canonical alias dictionary + normalization | Lower risk, auditable behavior, consistent with D-03/D-04 |

**Key insight:** Phase 3 is about trustable grounding, not maximizing recall through clever heuristics. Prefer deterministic, inspectable primitives.

## Common Pitfalls

### Pitfall 1: Alias registry is incomplete for historical variants
**What goes wrong:** RU/EN queries miss results for older team/driver naming conventions.  
**Why it happens:** Alias table is seeded only with modern names.  
**How to avoid:** Build canonical IDs with explicit alias arrays including RU transliterations and historical labels.  
**Warning signs:** Good EN recall but weak RU recall for known entities.

### Pitfall 2: Retrieval evidence exists but answer does not reference it
**What goes wrong:** API returns plausible answer and separate evidence blob without explicit linkage.  
**Why it happens:** Synthesis path ignores evidence IDs/ranks.  
**How to avoid:** Require synthesis function input to include evidence list and require output details to retain evidence used.  
**Warning signs:** Answers remain similar when evidence payload is altered.

### Pitfall 3: Metadata filters are not used
**What goes wrong:** Retrieval surfaces semantically similar but irrelevant seasons/events.  
**Why it happens:** Query uses plain vector similarity only.  
**How to avoid:** Add `where` filters for known canonical entity IDs, data source, and optionally season.  
**Warning signs:** Top-k includes unrelated eras despite strong alias match.

## Code Examples

Verified patterns from official sources:

### Chroma metadata filtering
```python
# Source: https://cookbook.chromadb.dev/core/filters/
results = collection.query(
    query_texts=[query],
    n_results=5,
    where={"entity_type": "driver", "canonical_id": {"$in": canonical_ids}},
)
```

### Pydantic response contract extension
```python
# Source: https://docs.pydantic.dev/latest/changelog/ (v2 stable line usage)
class NextMessageResponse(BaseModel):
    message: str
    status: Literal["ready", "failed"]
    details: dict = Field(default_factory=dict)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Prompt-only citation behavior | Deterministic retriever output + explicit evidence contract | Modern production RAG practice | Makes grounding testable and auditable |
| Monolingual alias assumptions | Cross-lingual normalization + canonical entity mapping | Became necessary with multilingual assistants | Reduces RU/EN retrieval asymmetry |
| Vector-only recall | Vector + metadata-constrained retrieval | Widely adopted in RAG hardening | Improves precision and traceability |

**Deprecated/outdated:**
- Blind fuzzy matching as primary resolver: high false-positive risk for trust-first domain responses.

## Open Questions

1. **Top-k and score thresholds for this corpus**
   - What we know: D-05 requires top-k evidence with rank score; threshold values are discretionary.
   - What's unclear: Exact values that balance precision/recall for RU/EN historical queries.
   - Recommendation: Add quick offline eval slice (10-20 canonical questions) and pick defaults empirically.

2. **Chunk size for `f1db` textual artifacts**
   - What we know: Retrieval snippets must be concise and traceable.
   - What's unclear: Optimal chunk length for this specific corpus shape.
   - Recommendation: Start with conservative chunk size and adjust by test evidence quality.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | backend runtime | ✓ | 3.14.0 | — |
| pip | dependency install | ✓ | 25.2 | — |
| pytest | validation architecture | ✓ | 9.0.2 | — |
| Node.js | GSD tooling in repo | ✓ | 24.11.1 | — |
| npm | JS package tooling | ✓ | 11.6.2 | — |
| Docker | optional integration testing/data tooling | ✓ | 28.5.2 | run local-only tests if unused |
| Chroma CLI | optional Chroma ops via CLI | ✗ | — | use Python `chromadb` client directly |

**Missing dependencies with no fallback:**
- None identified for Phase 3 implementation.

**Missing dependencies with fallback:**
- Chroma CLI missing; Phase 3 can proceed with Python SDK APIs.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | none — defaults currently used |
| Quick run command | `pytest tests/test_api_async_contracts.py -q` |
| Full suite command | `pytest -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RAG-01 | Answer uses Chroma-retrieved historical context | integration | `pytest tests/test_rag_grounding.py::test_historical_answer_uses_retrieved_context -q` | ❌ Wave 0 |
| RAG-02 | RU/EN aliases resolve to relevant retrieval hits | unit/integration | `pytest tests/test_alias_resolution.py -q` | ❌ Wave 0 |
| RAG-03 | Final response includes traceable evidence tied to synthesis | contract/integration | `pytest tests/test_rag_grounding.py::test_response_contains_traceable_evidence -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_api_async_contracts.py -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_alias_resolution.py` — covers `RAG-02`
- [ ] `tests/test_rag_grounding.py` — covers `RAG-01`, `RAG-03`
- [ ] Optional `pytest.ini` for markers/timeouts if integration tests expand

## Sources

### Primary (HIGH confidence)
- FastAPI release notes: https://fastapi.tiangolo.com/release-notes/ (verified `0.135.2` date line in official docs)
- Pydantic changelog: https://docs.pydantic.dev/latest/changelog/ (verified stable `v2.12.5`)
- Chroma overview docs: https://docs.trychroma.com/docs/overview/introduction (retrieval + metadata capabilities)
- Chroma filter cookbook: https://cookbook.chromadb.dev/core/filters/ (official filter grammar and examples)
- F1DB README: https://raw.githubusercontent.com/f1db/f1db/main/README.md (dataset scope and release cadence)

### Secondary (MEDIUM confidence)
- LangChain + Chroma usage patterns from community/issue references (used only as supplemental implementation signal)

### Tertiary (LOW confidence)
- General multilingual RAG blog posts from WebSearch (used only for pitfall framing, not normative architecture decisions)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - verified by installed environment + package index + official docs
- Architecture: HIGH - constrained by locked decisions and existing code contract boundaries
- Pitfalls: MEDIUM - partly supported by project research artifacts plus community multilingual RAG patterns

**Research date:** 2026-03-27
**Valid until:** 2026-04-26
