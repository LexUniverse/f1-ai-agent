---
phase: 3
slug: historical-rag-grounding
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-27
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | none — defaults currently used |
| **Quick run command** | `pytest tests/test_api_async_contracts.py -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_api_async_contracts.py -q`
- **After every plan wave:** Run `pytest -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | RAG-01 | integration | `pytest tests/test_rag_grounding.py::test_historical_answer_uses_retrieved_context -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | RAG-02 | unit/integration | `pytest tests/test_alias_resolution.py -q` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | RAG-03 | contract/integration | `pytest tests/test_rag_grounding.py::test_response_contains_traceable_evidence -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_alias_resolution.py` — stubs for `RAG-02`
- [ ] `tests/test_rag_grounding.py` — stubs for `RAG-01` and `RAG-03`
- [ ] Optional `pytest.ini` — markers/timeouts if integration tests expand

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
