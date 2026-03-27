---
phase: 04-ru-q-a-answer-reliability
plan: 01
subsystem: api
tags: pydantic, i18n, qna

requires:
  - phase: 03-historical-rag-grounding
    provides: EvidenceItem, retrieval wiring in next_message
provides:
  - Typed StructuredRUAnswer and QnAConfidence in API models
  - Deterministic Russian QnA builder from evidence
  - next_message success details include structured_answer and confidence
affects:
  - Phase 5 live enrichment (response shape consumers)

tech-stack:
  added: []
  patterns:
    - "Structured RU payload nested under details via model_dump()"

key-files:
  created:
    - src/answer/__init__.py
    - src/answer/russian_qna.py
  modified:
    - src/models/api_contracts.py
    - src/api/chat.py

key-decisions:
  - "Confidence tiers use fixed thresholds 0.65 / 0.40 on max rank_score over evidence."
  - "User-facing RU message line carries summary + tier; full structure lives in details."

patterns-established:
  - "Abstention branch leaves details free of structured_answer when RETRIEVAL_NO_EVIDENCE."

requirements-completed: [QNA-01, QNA-02]

duration: 15min
completed: 2026-03-27
---

# Phase 4 Plan 01 Summary

**Structured Russian QnA models and `/next_message` wiring deliver traceable citations and explicit confidence without changing the no-evidence abstention contract.**

## Performance

- **Duration:** ~15 min
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `QnAConfidence`, `AnswerSection`, and `StructuredRUAnswer` Pydantic models.
- Implemented deterministic `build_structured_ru_answer` and `qna_confidence_from_evidence` in `src/answer/russian_qna.py`.
- Success path now returns `structured_answer` and `confidence` in `details` plus an RU `message` with `Историческая сводка:` and `Уверенность:`.

## Task Commits

1. **Task 1: Pydantic models and Russian QnA builder** — `b1bf5d5`
2. **Task 2: Merge structured QnA into /next_message** — `1ac901a`

## Self-Check: PASSED

- `pytest tests/test_rag_grounding.py -q` passed after changes.
