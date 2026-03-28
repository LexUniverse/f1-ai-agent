---
phase: 13
slug: streamlit-unified-provenance-chat-ux
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-28
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — project default |
| **Quick run command** | `python3 -m pytest tests/test_provenance_display.py tests/test_streamlit_client.py -q` |
| **Full suite command** | `python3 -m pytest tests/ -q --ignore-glob='*integration*'` |
| **Estimated runtime** | ~15–60 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | UI-04 | grep + manual | `rg "messages\\.insert\\(0" streamlit_app.py` → no hits | ✅ | ⬜ pending |
| 13-01-02 | 01 | 1 | UI-05, UI-06 | grep + unit | `pytest tests/test_provenance_display.py -q` | ✅ W0 | ⬜ pending |
| 13-01-03 | 01 | 1 | UI-06 | grep | `rg "Происхождение ответа" streamlit_app.py` exits 0 | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_streamlit_client.py` — HTTP client contract tests
- [ ] `tests/test_provenance_display.py` — stubs for provenance predicate/formatting (added in plan wave 1)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Newest turn above composer | UI-04 | Streamlit layout | Run `streamlit run streamlit_app.py`; send 2+ turns; confirm oldest at top, latest above input |
| Single provenance expander | UI-06 | Visual | With API returning `provenance`, open «Происхождение ответа»; confirm no duplicate «Источники» for same RAG text |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
