# Phase 6: GigaChat Classic RAG - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 6-GigaChat Classic RAG
**Areas discussed:** Live branch vs GigaChat, `details` shape with LLM, template fallback transparency, confidence source

---

## Area selection

| Option | Description | Selected |
|--------|-------------|----------|
| Discuss area 1 only | Live branch routing | |
| Discuss area 2 only | Preserve schema vs message-primary | |
| Discuss area 3 only | Fallback signaling | |
| Discuss area 4 only | Confidence source | |
| Discuss all four | Full session | ✓ |

**User's choice:** `all` — all four gray areas selected.

**Notes:** Assistant had pre-annotated recommended defaults in the prior turn; user did not request deviations.

---

## 1. Live branch vs GigaChat

| Option | Description | Selected |
|--------|-------------|----------|
| A | Keep **live success path fully deterministic** (no GigaChat); GigaChat only when historical `evidence` is non-empty | ✓ |
| B | Run **GigaChat** on live success as well (single “LLM voice”) | |

**User's choice:** A (recommended default, confirmed implicitly by proceeding without objection after selecting all areas for discussion)

**Notes:** Aligns with Phase 5 contracts and avoids coupling fresh live data to model variability in v1.1.

---

## 2. `details` shape when LLM is primary

| Option | Description | Selected |
|--------|-------------|----------|
| A | **Preserve** `structured_answer` + `confidence` schema; map/validate LLM output into existing types | ✓ |
| B | **`message`-primary** narrative; minimal `details` as long as citations stay traceable | |

**User's choice:** A (recommended default)

**Notes:** Keeps Phase 7 / Streamlit and contract tests stable.

---

## 3. Template fallback transparency (GC-02)

| Option | Description | Selected |
|--------|-------------|----------|
| A | **Machine-readable** flag/metadata in `details` only | ✓ |
| B | A + **explicit Russian line** in `message` that synthesis used fallback | |
| C | **No extra signal** — indistinguishable OK payload aside from content | |

**User's choice:** A (recommended default; optional RU line left to Claude’s discretion in CONTEXT)

**Notes:** satisfies “documented fallback path” / explicit degraded signaling where appropriate without noisy UX.

---

## 4. Confidence when using GigaChat

| Option | Description | Selected |
|--------|-------------|----------|
| A | **Evidence-derived** tiers only (same philosophy as `qna_confidence_from_evidence`) | |
| B | **Model self-reported** confidence | |
| C | **Hybrid** — evidence baseline with optional caveats in structured sections | ✓ |

**User's choice:** C — evidence-derived baseline tier (**D-07**) plus optional qualitative caveats inside `structured_answer`; no higher tier without a tested rule.

**Notes:** Merges trust posture of Phase 4 with LLM nuance.

---

## Claude's Discretion

As captured in **06-CONTEXT.md**: client library choice, retries/timeouts, exact `details` key names for synthesis metadata, prompt language, and parsing/validation strategy for structured output.

## Deferred Ideas

None.
