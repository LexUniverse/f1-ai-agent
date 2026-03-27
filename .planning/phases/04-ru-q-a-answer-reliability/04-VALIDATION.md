---
phase: 4
slug: ru-q-a-answer-reliability
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (project) |
| **Config file** | none — existing `tests/` layout |
| **Quick run command** | `pytest tests/test_qna_reliability.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~15–45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_qna_reliability.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | QNA-01, QNA-02 | unit | `pytest tests/test_qna_reliability.py -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | QNA-01, QNA-02 | unit | `pytest tests/test_qna_reliability.py -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 2 | QNA-01, QNA-02, QNA-03 | integration | `pytest tests/test_qna_reliability.py tests/test_rag_grounding.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_qna_reliability.py` — stubs or full tests for QNA-01..03
- [ ] `tests/conftest.py` — reuse `client` fixture
- [ ] Existing pytest — no new framework install

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| RU copy reads naturally | QNA-01 | Subjective | Spot-check `message` and section text in dev after implementation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
