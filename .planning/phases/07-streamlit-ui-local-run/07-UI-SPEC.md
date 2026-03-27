# Phase 7 — UI design contract (Streamlit)

**Phase:** 07-streamlit-ui-local-run  
**Status:** Ready for implementation  
**Stack:** Streamlit (version pinned in `requirements.txt` during execution)

## 1. Copywriting (Dimension 1)

| Element | Text (RU) | Notes |
|---------|-----------|--------|
| Page title / header | «F1 Assistant» | Product-facing, short |
| Access code field | Label: «Код доступа»; placeholder: «Введите персональный код» | |
| Question field | Label: «Вопрос»; placeholder: «Например: кто выиграл Гран-при Монако в 1996?» | |
| Primary CTA | **«Отправить вопрос»** | Verb + noun; not «Submit» |
| New chat control | **«Новый чат»** | Clears `st.session_state` thread and session id (per D-11) |
| Waiting / polling | «Ожидаем ответ…» plus live **`message_status.status`** text | Per D-08 |
| Poll timeout | «Превышено время ожидания ответа (60 с). Проверьте, что API запущен на {base_url}.» | Concrete recovery path |
| Auth / HTTP error | Show `error.message` from envelope; prefix «Ошибка: » if plain | |

**Empty state (no messages yet):** Short hint: «Введите код и вопрос, затем нажмите «Отправить вопрос».»

## 2. Visual hierarchy (Dimension 2)

- **Primary anchor:** conversation thread (user bubbles / assistant blocks) in the main column.
- **Secondary:** compact «Уверенность» block directly under each assistant `message`.
- **Tertiary:** citations (`sources_block_ru`) as `st.markdown` or monospace-friendly block; **Live** and **synthesis** as `st.expander` defaults (per D-05, D-06).

## 3. Color & theme (Dimension 3)

- **Default Streamlit theme** — no custom accent palette required for v1.1.
- Reserve **primary button** only for «Отправить вопрос»; «Новый чат» as `st.button` secondary (not primary type).

## 4. Layout & density (Dimension 4)

- Main: chat history + response detail blocks.
- Sidebar optional for **advanced** base URL override — **not required** if env-only `F1_API_BASE_URL` is used (per D-01). Planner may place optional `st.sidebar.text_input` for base URL **or** document env-only.

## 5. Interaction (Dimension 5)

- **Submit:** validates non-empty access code and question before `POST /start_chat`.
- **Polling:** 0.75 s interval (within D-07 band 0.5–1.0 s), timeout 60 s (within D-08 band 30–60 s).
- **Terminal statuses:** on `ready` or `failed`, stop polling; then exactly one `POST /next_message` with `X-Session-Id` (per D-09).
- **New chat:** clears history keys and session id; does not call API until next submit.

## 6. Accessibility & feedback (Dimension 6)

- Use visible labels (not icon-only).
- On HTTP 4xx/5xx, show status code and envelope message in Russian-friendly layout.
- Spinner during poll: `st.spinner` tied to polling loop.

## API assumptions (UI-01)

- Client sends **`question`** in `/start_chat` JSON body when backend exposes `StartChatRequest.question` (minimal contract extension; see `07-RESEARCH.md`). If absent, backend keeps test default `next_message`.

## Traceability

- **UI-01..UI-03**, **D-01..D-11** from `07-CONTEXT.md`.

---

*UI-SPEC produced for plan-phase gate — 2026-03-27*
