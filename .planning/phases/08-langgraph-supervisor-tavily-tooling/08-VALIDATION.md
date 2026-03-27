---
phase: 8
slug: langgraph-supervisor-tavily-tooling
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-03-28
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | none — project default |
| **Quick run command** | `python3 -m pytest tests/test_f1_assistant_graph.py -q` (after Wave 1 adds file) |
| **Full suite command** | `python3 -m pytest` |
| **Estimated runtime** | ~30–90 seconds |

---

## Sampling Rate

- **After every task commit:** Run the **quick** command relevant to that task’s files (or `python3 -m pytest tests/test_<changed> -x`)
- **After every plan wave:** Run **`python3 -m pytest`**
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | AGT-01 | static | `rg "langgraph" requirements.txt` | ✅ | ⬜ pending |
| 08-01-02 | 01 | 1 | AGT-01, AGT-02 | unit | `python3 -m pytest tests/test_f1_assistant_graph.py -x` | ⬜ W1 | ⬜ pending |
| 08-01-03 | 01 | 1 | AGT-02 | unit | `python3 -m pytest tests/test_f1_assistant_graph.py -x` | ⬜ W1 | ⬜ pending |
| 08-02-01 | 02 | 2 | SRCH-01 | unit | `python3 -m pytest tests/test_gigachat_rag.py -x` | ✅ | ⬜ pending |
| 08-02-02 | 02 | 2 | AGT-01, SRCH-02 | integration | `python3 -m pytest tests/test_api_async_contracts.py tests/test_qna_reliability.py -x` | ✅ | ⬜ pending |
| 08-02-03 | 02 | 2 | SRCH-01, SRCH-02 | integration | `python3 -m pytest tests/test_tavily_turn.py -x` (new) | ⬜ W2 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Existing `pytest` + `tests/conftest.py` — no new framework install

*Wave 0 satisfied by current repo.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|---------------------|
| Real Tavily + GigaChat end-to-end | SRCH-01 | Network + secrets | Phase 10 TST-01 / optional env flag; not Phase 8 default CI |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or documented mock path
- [ ] Sampling continuity: graph tests run after Wave 1 tasks
- [ ] No watch-mode flags
- [ ] `nyquist_compliant: true` set in frontmatter when phase execution completes

**Approval:** pending
