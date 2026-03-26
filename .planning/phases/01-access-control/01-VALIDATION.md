---
phase: 1
slug: access-control
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_auth.py -x -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_auth.py -x -q`
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 1 | AUTH-01 | unit/integration | `pytest tests/test_auth.py::test_start_chat_valid_code_authorizes -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | AUTH-02 | unit/integration | `pytest tests/test_auth.py::test_start_chat_invalid_code_rejected -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | AUTH-02 | integration | `pytest tests/test_auth.py::test_unauthorized_blocked_before_chat_pipeline -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_auth.py` — stubs for AUTH-01 and AUTH-02
- [ ] `tests/conftest.py` — shared fixtures for session/auth requests
- [ ] `pip install pytest` — if framework not present

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
