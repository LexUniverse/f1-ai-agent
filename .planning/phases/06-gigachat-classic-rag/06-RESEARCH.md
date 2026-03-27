# Phase 6: GigaChat Classic RAG — Research

**Researched:** 2026-03-27  
**Domain:** GigaChat classic RAG (sync FastAPI `/next_message`), Pydantic API contracts, template fallback  
**Confidence:** HIGH for GigaChat SDK behavior (official README); MEDIUM for end-to-end JSON shaping (depends on model adherence)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

From **## Implementation Decisions** in `06-CONTEXT.md`:

- **D-01:** Historical-first retrieval and Phase 5 live gate unchanged: resolve → retrieve → format evidence → branch (non-empty evidence vs empty vs live).
- **D-02:** GigaChat applies to **both** historical success (non-empty evidence) and live-enriched success (empty evidence, live fetch OK). Historical path: prompt includes chunks/evidence. Live path: prompt includes `summarize_live_next_payload_ru` (and related live context) plus allowed chunk grounding; `details.live` populated when live data was used.
- **D-03:** Template fallback on GigaChat errors/unavailability uses equivalent deterministic builders from `russian_qna` so facts are not silently invented (GC-02).
- **D-04:** Preserve API contract: `structured_answer` as `StructuredRUAnswer`, `confidence` as `QnAConfidence` (`src/models/api_contracts.py`). Map or constrain GigaChat output (parse/validate; repair or retry — Claude’s discretion on strategy).
- **D-05:** `message` remains short primary Russian line for chat UIs; richer content in `structured_answer`.
- **D-06:** On template fallback after GigaChat failure: machine-readable `details` field (e.g. under `synthesis` / `model`) with `route: "template_fallback"` and optionally `gigachat_error_class`; fixed short Russian phrase in `message` disclosing non-LLM answer — wording once, pytest-stable.
- **D-07:** Hybrid confidence: `confidence.score` / `tier_ru` grounded in retrieval evidence when evidence exists (same family as `qna_confidence_from_evidence`); live-only may use `live_qna_confidence()` or documented variant. Model must not override numeric tier with self-reported confidence unless capped by evidence rules.
- **D-08:** Qualitative caveats only in `structured_answer.sections`, not conflicting `QnAConfidence`.

### Claude's Discretion

- GigaChat SDK wiring, timeouts, retry count before fallback, prompt templates (RU/EN system mix), JSON vs tool extraction for structured mapping.
- Exact `details` key names for synthesis metadata; exact Russian fallback disclosure string once tests lock it.
- How much historical chunk text is injected on the live branch when evidence is empty (minimal vs expanded) within prompt budget.

### Deferred Ideas (OUT OF SCOPE)

- **None** — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **GC-01** | With historical evidence, Russian answer via GigaChat using retrieved chunks in prompt; traceable citations in `details`. | Use `gigachat` `Chat` + `Messages` (official SDK); inject formatted evidence (same objects as today in `chat.py`); keep `evidence` in `details`; optional hybrid mapping so `sources_block_ru` / numbering stays aligned with `EvidenceItem` order. |
| **GC-02** | On GigaChat unavailable/errors, fallback to deterministic template with explicit degraded signaling. | Map `gigachat.exceptions` to fallback; set `details` synthesis route + fixed RU disclosure; reuse `build_structured_ru_answer` / `build_live_structured_ru_answer` / confidence helpers from `russian_qna.py`. |
| **GC-03** | Primary LLM RAG in `src/answer/gigachat_rag.py`; `russian_qna.py` helper/template only. | New module owns provider call + prompt assembly + parse/repair; `chat.py` orchestrates; `russian_qna.py` retains shared builders used by fallback (matches current `build_*`, `qna_confidence_from_evidence`, `summarize_live_next_payload_ru`, etc.). |
</phase_requirements>

## Project Constraints (from `.cursor/rules/`)

No rule files were present under `.planning` project `.cursor/rules/` at research time — no additional enforced directives beyond this phase’s CONTEXT.

## Summary

Phase 6 swaps **answer synthesis** in `src/api/chat.py` from pure template assembly (`build_structured_ru_answer` / live builders) to **GigaChat classic RAG**: the existing retrieval and live gate stay intact; a new **`src/answer/gigachat_rag.py`** performs sync completion calls with prompts that include **evidence snippets** and, on the live branch, **`summarize_live_next_payload_ru`-style live summary** per D-02.

The **canonical integration surface** for a FastAPI synchronous handler is the official **`gigachat`** SDK (`GigaChat` client, `timeout` / `max_retries` / env-based auth). **`langchain-gigachat`** remains valid for LangChain-native graphs but adds layering; the README explicitly warns against **double retry** when both SDK and framework retry — for a single sync call site, **`gigachat` alone** is the simpler default (aligned with “primary module” in `gigachat_rag.py`).

**Structured outputs:** API types `StructuredRUAnswer` and `QnAConfidence` in ```49:52:src/models/api_contracts.py
class StructuredRUAnswer(BaseModel):
    sections: list[AnswerSection]
    sources_block_ru: str
    citation_count: int
``` must remain the response shape. Research recommends a **hybrid mapping** consistent with D-07/D-08: compute **`QnAConfidence` with existing helpers** (`qna_confidence_from_evidence`, `live_qna_confidence`) instead of trusting model-reported scores; optionally build **`sources_block_ru` and `citation_count` deterministically** from the same `EvidenceItem` list passed to the client so citation IDs stay traceable to `details["evidence"]`. Let the model focus on **Russian section bodies** and a **short `message`** line.

**Primary recommendation:** Implement `gigachat_rag.py` with the **`gigachat`** package, env-driven credentials and TLS CA bundle, bounded retries, broad exception handling → template fallback with **machine-readable `details` + fixed Russian disclosure** in `message` (D-06); extend tests by **monkeypatching** the gigachat entrypoint (same style as `tests/test_qna_reliability.py`).

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| **gigachat** | **0.2.0** (PyPI latest verified 2026-03-27) | Sync/async chat completions, retries, typed errors | Official Sber client; documents env vars, timeouts, backoff; powers `langchain-gigachat`. |
| **pydantic** | 2.x (project) | `StructuredRUAnswer` / `QnAConfidence` validation | Already used in `api_contracts.py`; `model_validate_json` / `ValidationError` for repair loops. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|-------------|-------------|
| **langchain-gigachat** | 0.5.0 | `ChatGigaChat` Runnable | If you later unify with LangGraph nodes; not required for Phase 6 sync path. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Direct `gigachat` | `langchain-gigachat` | Extra abstraction; watch retry stacking (official README). |
| LLM-produced `sources_block_ru` | Deterministic builder from `evidence` | Deterministic reduces hallucinated `source_id`s; still satisfies traceability when bodies cite `[n]` matching `details.evidence` order. |

**Installation (pin when project gains a manifest — repo currently has no `pyproject.toml` / `requirements.txt` per Phase 5 research):**

```bash
pip install "gigachat==0.2.0"
```

**Version verification:** `pip index versions gigachat` → latest **0.2.0**; `langchain-gigachat` → **0.5.0** (2026-03-27).

## Architecture Patterns

### Recommended layout

```
src/
├── api/chat.py              # Orchestration: retrieve → try gigachat_rag → fallback
├── answer/
│   ├── gigachat_rag.py      # NEW: prompts, client call, parse → Partial/FullStructured
│   └── russian_qna.py       # Helpers + template fallback builders (GC-03)
├── models/api_contracts.py    # Unchanged shapes
└── retrieval/               # Unchanged
```

### Pattern 1: Sync GigaChat call from FastAPI

**What:** One request per `/next_message` success path; use context-managed `GigaChat` or a **single long-lived client** if you want to reuse OAuth token (planner choice: per-request vs app-scoped client on `app.state`).

**When:** GC-01/GC-02 hot path inside ```60:124:src/api/chat.py
@router.post("/next_message", response_model=NextMessageResponse)
def next_message(...)
``` (historical and live success branches).

**Example (from official README — patterns combined):**

```python
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole

# Env: GIGACHAT_CREDENTIALS, GIGACHAT_TIMEOUT, GIGACHAT_MAX_RETRIES, GIGACHAT_CA_BUNDLE_FILE, etc.
with GigaChat() as client:
    chat = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content="…instructions…"),
            Messages(role=MessagesRole.USER, content="…evidence + question…"),
        ],
    )
    response = client.chat(chat)
    text = response.choices[0].message.content
```

**Source:** [GigaChat Python SDK README](https://github.com/ai-forever/gigachat/blob/main/README.md) (Configuration, Basic Chat, Function Calling example for `Chat`).

### Pattern 2: Classic RAG prompt (evidence + optional live)

**What:** System message: Russian answer rules, cite only provided context, JSON or structured delimiter rules. User message: enumerated chunks with stable indices `[1]..[n]` matching `details.evidence` order; live branch adds **“Актуальные данные (не из исторической базы): …”** plus output of `summarize_live_next_payload_ru` (existing helper in ```46:61:src/answer/russian_qna.py
def summarize_live_next_payload_ru(payload: dict) -> str:
```).

**When:** D-02 both branches.

### Pattern 3: Hybrid mapping to Pydantic (recommended)

**What:**

1. Parse model output (JSON preferred) for **sections** and maybe **`message`**.
2. Set **`confidence`** via `qna_confidence_from_evidence(evidence)` or `live_qna_confidence()` (never raw LLM “confidence”).
3. Build **`sources_block_ru`** / **`citation_count`** via the same logic as ```23:36:src/answer/russian_qna.py
def build_structured_ru_answer(evidence: list[EvidenceItem]) -> StructuredRUAnswer:
``` (or extract a tiny shared function to avoid duplication).

**Why:** Satisfies D-07/D-08 and GC-01 traceability with minimal hallucination surface on `source_id`.

### Anti-patterns to avoid

- **Double retry:** SDK `max_retries > 0` and LangChain retries both on — **multiplies attempts** (README warning).
- **Silent fallback:** Returning template answers without D-06 **`details` route** and **disclosure** in `message`.
- **LLM-overwritten confidence:** Letting the model set `QnAConfidence` tiers that contradict retrieval scores (violates D-07).
- **Uncapped prompt on live path:** Dumping huge payloads; trim snippets (retrieval already caps at `SNIPPET_MAX_LEN` in ```3:4:src/retrieval/evidence.py
SNIPPET_MAX_LEN = 280
```).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP + OAuth to GigaChat | Raw `httpx` OAuth flow | **`gigachat.GigaChat`** | Token refresh, TLS, retries, typed errors already implemented. |
| Transient 429/5xx handling | Ad-hoc sleep loops | **`max_retries` / `retry_backoff_factor` / `retry_on_status_codes`** | SDK-native; tune once (watch interaction with app-level retry). |
| Russian TLS chain | Disable verify globally in prod | **`GIGACHAT_CA_BUNDLE_FILE` / `ca_bundle_file`** | Official guidance for Russian Ministry CA. |

**Key insight:** The SDK is the supported integration path; custom HTTP stacks duplicate auth and certificate behavior.

## Common Pitfalls

### Pitfall 1: TLS / CA on developer laptops

**What goes wrong:** SSL handshake or verify errors outside Russia without the Gosuslugi root CA.  
**Why:** Python uses bundled CAs, not necessarily the Russian chain.  
**How to avoid:** Set `GIGACHAT_CA_BUNDLE_FILE` per README; document in PROJECT/local run.  
**Warning signs:** Exceptions wrapping certificate errors on first `chat()`.

### Pitfall 2: Python runtime vs SDK claim

**What goes wrong:** Local dev on **Python 3.14** while README states support **3.8–3.13**.  
**Why:** Classifiers may lag; wheels may not exist.  
**How to avoid:** Run CI and recommended local env on **3.12 or 3.13**; verify `import gigachat` in target image before planning “done.”  
**Warning signs:** Install or import failure on 3.14.

### Pitfall 3: JSON schema drift

**What goes wrong:** Model returns prose instead of JSON; partial keys; wrong `citation_count`.  
**Why:** LLMs ignore format instructions under pressure.  
**How to avoid:** One **repair** completion with `ValidationError` summary; then **template fallback** (D-03) if still invalid; or use **function calling** (`Function` in README) if planners accept tool-schema coupling.  
**Warning signs:** Frequent `ValidationError` in logs.

### Pitfall 4: Breaking pytest stability

**What goes wrong:** Tests assert exact legacy template strings (e.g. `tests/test_qna_reliability.py` “Историческая сводка:”).  
**Why:** GigaChat path changes `message` wording.  
**How to avoid:** Mock `gigachat_rag.synthesize_*` to return deterministic fixtures **or** split assertions: template fallback vs LLM success.  
**Warning signs:** Full suite red after wiring real prompts.

## Code Examples

### Exception mapping for fallback (official exception list)

```python
from gigachat.exceptions import (
    GigaChatException,
    AuthenticationError,
    RateLimitError,
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    RequestEntityTooLargeError,
    ServerError,
)
```

**Source:** [GigaChat Python SDK README — Error Handling](https://github.com/ai-forever/gigachat/blob/main/README.md)

### Env-based configuration (ops-friendly)

Per README: `GIGACHAT_CREDENTIALS`, `GIGACHAT_TIMEOUT`, `GIGACHAT_MAX_RETRIES`, `GIGACHAT_RETRY_BACKOFF_FACTOR`, `GIGACHAT_MODEL`, `GIGACHAT_VERIFY_SSL_CERTS`, `GIGACHAT_CA_BUNDLE_FILE`.

### Retry defaults

Constructor defaults: `timeout=30.0`, `max_retries=0`. For Phase 6, set explicit **`max_retries`** (e.g. 2–3) **or** keep 0 and retry once at orchestration level — but **not both** duplicated blindly.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Template-only synthesis in `chat.py` | GigaChat RAG + template fallback | Phase 6 | Richer RU answers; operational dependency on GigaChat + CA setup. |
| Single-source template `message` | LLM `message` + structured sections | Phase 6 | UI copy may need tolerance for variation unless mocked in tests. |

**Deprecated / caution:** SDK README deprecates `Messages.data_for_context` — put context in message text (classic RAG fits this).

## Open Questions

1. **Per-request vs shared `GigaChat` client on `app.state`?**
   - What we know: Token fetch on first use; `get_token()` can pre-auth.
   - What’s unclear: Desired connection reuse under load.
   - Recommendation: Start per-request context manager; optimize to shared client if OAuth chatter becomes noisy.

2. **Full JSON `StructuredRUAnswer` from model vs hybrid (sections only)?**
   - What we know: Hybrid aligns with D-07/D-08 and citation safety.
   - What’s unclear: Product want for model-authored source blurbs.
   - Recommendation: Hybrid default; document if product later wants full generative `sources_block_ru`.

## Environment Availability

**Step 2.6 executed:** external dependencies identified.

| Dependency | Required By | Available (research host) | Version | Fallback |
|------------|-------------|---------------------------|---------|----------|
| Python runtime | Project | ✓ | 3.14.0 | Use **3.12–3.13** per GigaChat README support band |
| pytest | Tests | ✓ | 9.0.2 | — |
| **gigachat** package | GC-01 | Not verified installed | — | `pip install gigachat==0.2.0` |
| **GigaChat API credentials** | GC-01 live calls | ✗ (secrets) | — | Tests use mocks; humans set `GIGACHAT_CREDENTIALS` |
| **Russian CA bundle file** | TLS verify | ✗ (path-specific) | — | `GIGACHAT_CA_BUNDLE_FILE` or dev `GIGACHAT_VERIFY_SSL_CERTS=false` (not prod) |

**Missing dependencies with no fallback:**

- Valid credentials for real integration testing (treat as manual / skipped test).

**Missing dependencies with fallback:**

- **Package not installed** → Wave 0 / plan: add dependency pin when manifest exists.
- **No network in CI** → Mock `gigachat_rag` (GC-02 still tested via forced failure path).

## Validation Architecture

> `workflow.nyquist_validation` is **true** in `.planning/config.json` — section required.

### Test framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x (local probe) |
| Config file | `pytest.ini` (`-p no:lazy-fixture`) |
| Quick run command | `pytest tests/test_gigachat_rag.py -x` (after file exists) |
| Full suite command | `pytest` |

### Phase requirements → test map

| Req ID | Behavior | Test type | Automated command | File exists? |
|--------|----------|-----------|-------------------|--------------|
| **GC-01** | With evidence, orchestration calls GigaChat path (or mocked) and returns `structured_answer` + `evidence` with aligned citations | unit + API | `pytest tests/test_gigachat_rag.py tests/test_qna_reliability.py -x` | ❌ Wave 0: add `test_gigachat_rag.py`; update reliability tests for LLM vs template |
| **GC-02** | On configured failure (mock raise), response matches template + `details` contains fallback route + disclosure phrase in `message` | unit + API | `pytest tests/test_gigachat_fallback.py -k fallback -x` | ❌ Wave 0 — or consolidate in `test_gigachat_rag.py` |
| **GC-03** | `gigachat_rag` module owns synthesis entrypoint; `russian_qna` only helpers; import graph sane | unit / smoke | `pytest tests/test_gigachat_rag.py::test_primary_module_import -x` | ❌ Wave 0 |

### Sampling rate

- **Per task commit:** `pytest tests/test_gigachat_rag.py -x` (narrow)
- **Per wave merge:** `pytest`
- **Phase gate:** full suite green before `/gsd-verify-work`

### Wave 0 gaps

- [ ] `tests/test_gigachat_rag.py` — mock `GigaChat.chat` **or** monkeypatch `src.answer.gigachat_rag.<entrypoint>`; assert **no real network**
- [ ] Extend `tests/test_qna_reliability.py` / `tests/test_live_enrichment.py` — **monkeypatch** gigachat synthesis to deterministic fixture **or** assert new contracts (fallback disclosure when patch forces failure)
- [ ] Document `pip install gigachat==0.2.0` when repo adds `requirements.txt` / `pyproject.toml`
- [ ] Optional: `pytest.mark.integration` + skip without `GIGACHAT_CREDENTIALS` for manual RAG smoke

### Mocking patterns (align with existing tests)

Existing tests monkeypatch **`src.api.chat.resolve_entities`** and **`retrieve_historical_context`** (see ```8:17:tests/test_qna_reliability.py
    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
```). **Add** `monkeypatch.setattr("src.api.chat.<gigachat_entrypoint>", fake)` or patch at `gigachat_rag` module level so GC-01/02 are fast and deterministic.

**GC-02 disclosure:** Store the exact Russian substring in a **module-level constant** (e.g. `GIGACHAT_TEMPLATE_FALLBACK_DISCLOSURE_RU`) and assert `assert disclosure in payload["message"]` for fallback tests.

## Sources

### Primary (HIGH confidence)

- [GigaChat Python SDK README](https://github.com/ai-forever/gigachat/blob/main/README.md) — auth env vars, `timeout`, `max_retries`, TLS CA, exception types, double-retry warning, `Chat`/`Messages` API
- [GigaChat REST API docs](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/gigachat-api) — referenced from README (domain reference)
- Project files: `06-CONTEXT.md`, `src/api/chat.py`, `src/answer/russian_qna.py`, `src/models/api_contracts.py`, `src/retrieval/evidence.py`

### Secondary (MEDIUM confidence)

- `.planning/research/STACK.md` — version alignment `gigachat==0.2.0` / `langchain-gigachat==0.5.0`
- Existing pytest patterns under `tests/test_qna_reliability.py`, `tests/test_live_enrichment.py`, `tests/conftest.py`

### Tertiary (LOW confidence)

- Whether **Python 3.14** gains official support before v1.1 ships — treat as **environment risk**; prefer 3.12/3.13 for development.

## Metadata

**Confidence breakdown:**

- Standard stack: **HIGH** — PyPI + official README
- Architecture: **HIGH** — grounded in current `chat.py` + CONTEXT
- Pitfalls: **MEDIUM-HIGH** — TLS and JSON adherence are recurring class of issues

**Research date:** 2026-03-27  
**Valid until:** ~2026-04-27 (SDK 0.2.x); re-check if `gigachat` 1.0 or API breaks land

## RESEARCH COMPLETE
