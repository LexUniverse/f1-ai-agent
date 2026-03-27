---
phase: 2
slug: async-backend-contracts
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + FastAPI TestClient |
| **Config file** | none — defaults currently used |
| **Quick run command** | `pytest tests/test_api_async_contracts.py -x` |
| **Full suite command** | `pytest -x` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_api_async_contracts.py -x`
- **After every plan wave:** Run `pytest -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 1 | API-01 | integration | `pytest tests/test_api_async_contracts.py::test_start_chat_returns_uuid_session_id -x` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | API-04 | integration | `pytest tests/test_api_async_contracts.py::test_invalid_payload_returns_enveloped_validation_error -x` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 2 | API-02 | integration | `pytest tests/test_api_async_contracts.py::test_message_status_returns_structured_state -x` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 2 | API-03 | integration | `pytest tests/test_api_async_contracts.py::test_next_message_contract_flow -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_api_async_contracts.py` — API-01..API-04 contract tests
- [ ] `tests/helpers.py` or shared assertions in `tests/conftest.py` for envelope validation
- [ ] Status lifecycle assertions for `queued -> processing -> ready | failed`

---

## Manual-Only Verifications

All phase behaviors should have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
