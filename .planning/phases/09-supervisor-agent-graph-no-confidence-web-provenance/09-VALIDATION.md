---
phase: 9
slug: supervisor-agent-graph-no-confidence-web-provenance
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` or default pytest |
| **Quick run command** | `python -m pytest tests/test_f1_supervisor_graph.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~30–120 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command for touched tests
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite green

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 09-01-* | 01 | 1 | AGT-03–05, SRCH-03 | unit | `pytest tests/test_f1_supervisor_graph.py` | ⬜ |
| 09-02-* | 02 | 2 | API-05, WEB-01 | unit | `pytest tests/test_*chat*` or new contract test | ⬜ |

---

## Wave 0 Requirements

- Existing pytest infrastructure covers baseline; **no Wave 0 install** unless executor discovers missing deps.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GigaChat live quality | SRCH-03 | Cloud model variability | Ask “кто победил в сезоне 2021?” with real keys; expect name in `message`, not query echo. |

---

## Validation Sign-Off

- [ ] Supervisor graph tests green
- [ ] No `confidence` in sample `/next_message` JSON
- [ ] `nyquist_compliant: true` after execution

**Approval:** pending
