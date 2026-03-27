# Phase 4: RU Q&A Answer Reliability - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `04-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 4 — RU Q&A Answer Reliability
**Areas discussed:** Structured answer shape, Confidence, Citations, Abstention / insufficient evidence

---

## Area selection

| Option | Description | Selected |
|--------|-------------|----------|
| 1 — Structured answer shape | API + UX for QNA-01 | ✓ |
| 2 — Confidence | Scale and semantics for QNA-02 | ✓ |
| 3 — Citations | Presentation and traceability for QNA-02 | ✓ |
| 4 — Abstention | QNA-03 vs current `failed` behavior | ✓ |

**User's choice:** Discuss all four areas (1, 2, 3, 4).

---

## 1 — Structured answer shape

| Option | Description | Selected |
|--------|-------------|----------|
| A | Typed `details` + short RU `message` | ✓ |
| B | `message` only + template; minimal `details` beyond evidence | |
| C | Full parity: typed `details` and mirrored long `message` | |

**User's choice:** **1A**

**Notes:** Structured blocks live in `details`; `message` remains the concise Russian line for chat.

---

## 2 — Confidence

| Option | Description | Selected |
|--------|-------------|----------|
| A | Three RU tiers only, rule-based from retrieval | |
| B | Numeric in `details` + RU tier | |
| C | Claude’s discretion: tier ± optional numeric, documented in planning | ✓ |

**User's choice:** **2C**

**Notes:** Planner/implementer defines exact mapping; user-facing Russian confidence always required.

---

## 3 — Citations

| Option | Description | Selected |
|--------|-------------|----------|
| A | Inline `[n]` + optional «Источники» | |
| B | Trailing sources block only | |
| C | Claude’s discretion between A/B; must tie claims to `evidence[]` | ✓ |

**User's choice:** **3C**

**Notes:** Sub-prompt **3b** (RU/EN/mixed labels) was not answered; `04-CONTEXT.md` records default **RU-first** visible text with EN/raw ids in evidence.

---

## 4 — Abstention / insufficient evidence

| Option | Description | Selected |
|--------|-------------|----------|
| A | `ready` + abstention when evidence thin; `failed` for hard errors | |
| B | Keep current: insufficient evidence → `failed` + e.g. `RETRIEVAL_NO_EVIDENCE` | ✓ |
| C | Hybrid: zero evidence → `failed`; weak evidence → `ready` + hedge | |

**User's choice:** **4B**

**Notes:** Aligns with existing `chat.py` behavior for empty retrieval.

---

## Claude's Discretion

- Confidence mapping (2C).
- Citation layout (3C).
- Default for source labeling (3b): RU-first + retain EN/raw evidence fields.

## Deferred Ideas

None recorded in this session.
