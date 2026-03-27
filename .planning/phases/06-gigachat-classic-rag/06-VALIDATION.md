---
phase: 6
slug: gigachat-classic-rag
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | `pytest.ini` (`addopts = -p no:lazy-fixture`) |
| **Quick run command** | `pytest tests/test_gigachat_rag.py -x` (after Wave 0 creates file) |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~30–90 seconds (full suite; varies with index tests) |

---

## Sampling Cadence

- **After every task commit:** `pytest tests/test_gigachat_rag.py -x` (narrow) when that module exists
- **After every plan wave:** `pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** Under 2 minutes for quick path on dev laptop

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | GC-03 | unit | `pytest tests/test_gigachat_rag.py -x` | ❌ Wave 0 | ⬜ pending |
| 06-01-02 | 01 | 1 | GC-01 | unit | `pytest tests/test_gigachat_rag.py tests/test_qna_reliability.py -x` | Partial | ⬜ pending |
| 06-02-01 | 02 | 2 | GC-02 | unit | `pytest tests/test_gigachat_rag.py -k fallback -x` | ❌ Wave 0 | ⬜ pending |
| 06-02-02 | 02 | 2 | GC-01, GC-02 | integration | `pytest tests/ -x` (after monkeypatch updates) | ✅ infra | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_gigachat_rag.py` — mocks for GigaChat / `gigachat_rag` entrypoint; **no real network**; covers GC-01 happy path and GC-02 forced failure → template + disclosure
- [ ] Updates to `tests/test_qna_reliability.py` and/or `tests/test_live_enrichment.py` — tolerate LLM path via monkeypatch or branch on synthesis route
- [ ] Optional: `pytest.mark.integration` test skipped without `GIGACHAT_CREDENTIALS` for manual smoke

*Dependency pin:* document `gigachat==0.2.0` when repo adds `requirements.txt` or `pyproject.toml`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real GigaChat TLS + credentials | GC-01 | Secrets + CA path per machine | Set `GIGACHAT_CREDENTIALS` and optional `GIGACHAT_CA_BUNDLE_FILE`; call `/next_message` with evidence; confirm non-fallback `details` |

*All other phase behaviors target automated verification via mocks.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency within target
- [ ] `nyquist_compliant: true` set in frontmatter when complete

**Approval:** pending
