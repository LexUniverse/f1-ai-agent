# Phase 6: GigaChat Classic RAG - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 6-GigaChat Classic RAG
**Areas discussed:** Live branch vs GigaChat; `details` shape with LLM; Template fallback transparency; Confidence with GigaChat

---

## Live branch vs GigaChat

| Option | Description | Selected |
|--------|-------------|----------|
| A | Live-enriched success stays **deterministic only** (no GigaChat on live path). | |
| B | **Also** call GigaChat on live success — prompt includes live summary (and optional chunk context). | ✓ |

**User's choice:** B  
**Notes:** Aligns historical and live success behind one synthesis voice; implementation must preserve `details.live` and Phase 5 freshness semantics.

---

## `details` shape (LLM primary)

| Option | Description | Selected |
|--------|-------------|----------|
| A | **Preserve** `StructuredRUAnswer` + `QnAConfidence` strictly (parse/validate model output). | ✓ |
| B | `message`-primary; thinner structured fields if citations traceable. | |

**User's choice:** A  
**Notes:** Keeps Phase 4/7 contract stability; planner defines parsing/repair strategy.

---

## Template fallback transparency

| Option | Description | Selected |
|--------|-------------|----------|
| A | Machine-readable flag in `details` only. | |
| B | Machine-readable flag **plus** short **fixed Russian** user-visible line. | ✓ |
| C | No extra signaling beyond current template behavior. | |

**User's choice:** B  
**Notes:** Satisfies explicit degraded signaling “where appropriate” for GC-02; string must be test-stable once chosen.

---

## Confidence with GigaChat

| Option | Description | Selected |
|--------|-------------|----------|
| A | Evidence-derived only. | |
| B | Model drives tier/score. | |
| C | **Hybrid** — evidence grounds/caps tier; model caveats only in `structured_answer` sections. | ✓ |

**User's choice:** C  
**Notes:** Avoids overconfident LLM numeric tiers while allowing nuance in prose sections.

---

## Claude's Discretion

Exact `details` keys for synthesis metadata; GigaChat timeouts/retries; prompt design; fallback RU disclosure wording; chunk depth on live-only prompts.

## Deferred Ideas

None.
