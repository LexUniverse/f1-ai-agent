---
status: passed
phase: 13-streamlit-unified-provenance-chat-ux
updated: 2026-03-28
---

# Phase 13 Verification

## Must-haves

| Criterion | Evidence |
|-----------|----------|
| UI-04 chronological append; oldest top, newest above composer | `streamlit_app.py` uses `messages.append` for user then assistant; transcript loop is forward order |
| UI-05 answer body before expanders | `_render_assistant_block` calls `st.markdown(content)` first |
| UI-06 single «Происхождение ответа» with Russian subsections when `provenance` usable | Unified branch: expander + `### Контекст (RAG)`, `### Веб-поиск`, optional `### Загрузка страницы`, `### Синтез`; legacy path skips duplicate blocks when unified applies |
| D-07 live expander label | `st.expander("Актуальные данные (live)", …)` |
| Legacy fallback when no usable provenance | `else` branch retains Источники, `st.json(web)`, Синтез expanders |

## Automated

- `python3 -m pytest tests/test_provenance_display.py tests/test_streamlit_client.py -q` — pass
- `python3 -m pytest tests/ -q --ignore-glob='*integration*'` — 67 passed (2026-03-28)

## human_verification

_Optional: run Streamlit against API with a turn that returns `details.provenance` and confirm one expander and Russian labels._
