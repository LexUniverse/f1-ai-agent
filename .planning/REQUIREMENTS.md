# Requirements: F1 Assistant (GigaChat + LangGraph)

**Defined:** 2026-03-26 / **v1.4 scoped:** 2026-03-28 / **v1.5 scoped:** 2026-03-28 / **v1.6 scoped:** 2026-03-28  
**Core Value:** The assistant knows Formula 1 deeply and delivers accurate answers with minimal hallucinations.

## v1.6 Requirements (milestone active)

Инструменты агента: **время «сейчас»** с [TimeAPI.io](https://www.timeapi.io/swagger/index.html) и **следующий гран-при / сессии** из [FastF1](https://github.com/theOehrly/Fast-F1) `EventSchedule` относительно этой метки. Нумерация фаз на роадмапе продолжается после **16**.

### Time API

- [ ] **TIME-01**: Бэкенд или воркер вызывает **TimeAPI.io** для **текущего UTC** (и/или unix через `GET /api/v1/time/current/unix` / `.../utc` — см. [Swagger](https://www.timeapi.io/swagger/index.html)): **таймаут**, **одна** попытка или согласованный retry в плане; при недоступности — **фиксированное** русскоязычное degraded-сообщение или безопасный fallback **только если** явно описан в плане (по умолчанию предпочтительно не подменять серверное время локальным без согласования).

### F1 schedule (FastF1)

- [ ] **SCHED-01**: По **году сезона** (по умолчанию год по UTC с **TIME-01**, либо параметр инструмента) загружается **`fastf1.get_event_schedule(year)`** (или эквивалент `EventSchedule`). Из расписания выбирается **следующее событие гран-при** (`RoundNumber > 0`, не `testing`), у которого **время следующей релевантной сессии** (например первая будущая `Session*DateUtc` или `EventDate`) **строго после** момента «сейчас» с **TIME-01**. В структурированном ответе инструмента: **название этапа**, **страна/трасса** (как в FastF1), **UTC даты/времена сессий** для предстоящего уик-энда (или согласованное подмножество). Учесть ограничения FastF1 для **ergast** и сезонов **до 2018** в документации и в плане верификации.

### Agent tools & UX

- [ ] **TOOL-01**: В графе LangGraph доступны **два** (или один объединённый, если план так проще) **tool** для GigaChat-воркера: получение **текущего времени** (обёртка над **TIME-01**) и получение **следующего ГП / расписания сессий** (обёртка над **SCHED-01**). Воркер использует их для вопросов о **предстоящих гонках** и **«сейчас»** без выдумывания дат. **Поведение при ошибке TimeAPI** не ломает остальной граф (явная ошибка инструмента → воркер/supervisor как для других tools). Опционально в **details** фиксируется использование schedule/time tools (если согласовано с **WEB-02** / provenance — в плане фазы).

---

## v1.5 Requirements (phases 15–16 — still on roadmap)

Phases **14–16** on the roadmap. **Supersedes** the deferred v1.4 **Phase 14** (README/smokes-only) by folding **DOC-01** and **TST-01** into **v1.5 Phase 16** alongside **DOC-02**.

### RAG & index (Phase 14)

- [x] **RAG-08**: **Corpus design — explicit table whitelist** (no “все CSV”): **`f1db-races.csv`**, **`f1db-seasons-drivers.csv`**, **`f1db-drivers.csv`**, **`f1db-races-race-results.csv`**, plus low-noise reference tables **`f1db-grands-prix.csv`**, **`f1db-circuits.csv`**, **`f1db-constructors.csv`**, **`f1db-seasons.csv`**, **`f1db-seasons-driver-standings.csv`** (чемпионат по годам через `championshipWon` / позиции). **Не индексировать** крупные «шумные» ленты (пит-стопы, все сессии практик/квалификаций, **`f1db-races-driver-standings.csv`** ~21k и т.п.) без отдельного обоснования в плане. Улучшить **document_text**: осмысленные **английские** предложения/факты из строки (и при необходимости склейка полей), стабильные `source_id` / metadata. **RU ↔ EN:** жёсткий билингвальный текст в каждом чанке **не обязателен**; допустимы **любые сочетания**, выбранные в плане: нормализация/перевод **запроса** на EN (GigaChat), лёгкие словари алиасов ГП/трасс, гибрид с узким **structured / filter** поверх метаданных Chroma — с учётом **орфографии** (fuzzy / несколько вариантов запроса / одна LLM-нормализация). Зафиксировать выбранный подход в **README** / **README_DETAILED** (фаза 16).
- [x] **RAG-09**: **Verification** — автоматические или скриптовые проверки, что для **Monaco 2000 winner** и **2021 drivers’ champion** после retrieval (и выбранной нормализации запроса) находятся релевантные чанки; пороги/фикстуры — стабильные для CI.

### Supervisor & web (Phase 15)

- [ ] **AGT-08**: **Supervisor contract** — на вход для решения **accept/reject** подаётся **только** сопоставление **вопрос пользователя ↔ готовый кандидат-ответ** (и технический JSON по схеме). **Не** передавать супервизору канал происхождения (RAG / web / только title/snippet / fetch): он **не оценивает источник**, только **отвечает ли текст вопросу**. Ответ пользователю по-прежнему **прямой русский ответ** или **abstention** (AGT-05); **никаких** ответов вопросом на вопрос.
- [ ] **AGT-09**: **Web chain (один Tavily на ход)** — порядок фиксирован: **(1)** RAG-кандидат → супервизор: достаточно ли для ответа; **(2)** если нет — **один** Tavily; **GigaChat** решает, достаточно ли **title/snippet** у выдачи для ответа; **(3)** если недостаточно — **GigaChat** выбирает **до двух** URL по релевантности **заголовков** (и при необходимости сниппетов); **последовательные bounded fetch’и: максимум 2** — сначала первый URL, если после извлечённого текста фактов всё ещё не хватает — второй; агрегированный лимит времени/байт на оба fetch’а; **один** итоговый кандидат на повторную оценку супервизором. *(Расширяет Phase 12 **AGT-07**, где был «ровно один fetch».)*
- [ ] **SRCH-05**: **Title/snippet как полноценное основание** — воркер может синтезировать ответ **только** из title/snippet, если факт в них явно выражен; супервизор **может принять** такой кандидат так же, как любой другой (**AGT-08**). Не предпочитать заведомо худший URL лучшему по заголовку.

### Documentation & quality (Phase 16)

- [ ] **DOC-01**: **README** — clone/setup, env, index/build, API + Streamlit commands, **`.env` / `.env.example`** with acquisition links.
- [ ] **DOC-02**: **`README_DETAILED.md`** — narrative map of **`src/`** modules, LangGraph nodes, retrieval pipeline, API contracts, Streamlit client, and how **f1db-csv** flows into Chroma.
- [ ] **TST-01**: **Pytest** opt-in smokes (marker + env) for live GigaChat/Tavily; default CI **offline/mocked**.

---

## v1.4 Requirements (milestone closed — phases 12–13)

**Supersedes** the unfinished **v1.3 roadmap phases 10–11** by merging Streamlit + docs with new orchestration and UI work. Phases **12–13** delivered; original **Phase 14** (docs only) **moved to v1.5 Phase 16**.

### Supervisor & acceptance (Phase 12)

- [x] **AGT-06**: **Accept/reject** is determined **only** by the **supervisor LLM** (GigaChat JSON). **Audit** the codebase for any **numeric thresholds** (e.g. legacy 0.55-style gates) on the **accept path**; remove or document if unrelated to the removed product `confidence` field. **Tune** parse-failure policy (currently conservative `False`) so real API errors are distinguishable from **avoidable false rejects**.
- [x] **AGT-07**: After the **initial RAG-only** candidate, the worker may use the **web tool at most once per turn** (one Tavily query). **No second** Tavily iteration. **Deepening** happens inside that pass: **rank** returned URLs, assess **titles/snippets**; if insufficient, **fetch exactly one** operator-chosen URL (HTTP, bounded) and incorporate extracted text into **one** revised candidate before the supervisor sees it again. If still rejected, **AGT-05** terminal message (same user-facing copy unless plan agrees a tweak).

### Search & synthesis (Phase 12)

- [x] **SRCH-04**: Worker **selects** the best-matching result(s) from the Tavily list for the user question; **prefers** an answer from **titles/snippets** when they suffice; **escalates** to **single-page** content only when needed.

### API / provenance (Phase 12–13)

- [x] **WEB-02**: Response **`details`** expose a **single structured surface** suitable for UI: **RAG** evidence (snippets/source ids) and **web** (query, URLs, titles, snippets, optional **fetch** metadata) without duplicating the same URLs in multiple unrelated keys. *(Extends **WEB-01**.)*

### Streamlit (Phase 13)

- [x] **UI-04**: Chat history **chronological** (oldest top, **newest** above composer); turns **appended**.
- [x] **UI-05**: Assistant **message** body always visible; **no** confidence UI (**API-05**).
- [x] **UI-06**: **One** collapsed **«Происхождение ответа»** (or agreed label) expander containing **RAG context**, **web** provenance, and **synthesis route / metadata** — **no** separate duplicate «Источники» blocks + separate web JSON expander + vague «Синтез»-only labels for the same content.

### Documentation & quality (was Phase 14 — see v1.5)

_Moved to **v1.5 Phase 16** (**DOC-01**, **TST-01**) + **DOC-02**._

---

## v1.3 Requirements (milestone core — delivered Phase 9)

Scoped 2026-03-28 — supervisor loop, no product confidence, `details.web`. *(Phases 10–11 moved to v1.4.)*

### Orchestration — supervisor & Agent 1 (Phase 9)

- [x] **AGT-03**: LangGraph + LangChain tools; **supervisor** evaluates **candidate answer** vs **user question**; accept/reject.
- [x] **AGT-04**: *(v1.3 wording)* RAG-first, then **up to two** Tavily-backed revisions — **superseded by AGT-07** in v1.4 (one Tavily + optional fetch).
- [x] **AGT-05**: Fixed Russian terminal message after exhausted search-backed attempts — **still required**; **exhaustion** definition updates to **AGT-07** (one Tavily pass).

### Web search & answer quality (Phase 9)

- [x] **SRCH-01**, **SRCH-02** — Phase 8 / folded into Agent 1.
- [x] **SRCH-03**: Accepted **`message`** answers the **original** question; not query-echo / sources-only.

### API contract (Phase 9)

- [x] **WEB-01**: **`details.web`** when search contributed.
- [x] **API-05**: No **`confidence`** in public shapes.

### Streamlit / docs (were Phase 10–11 — now v1.4 / v1.5)

- UI: **UI-04, UI-05, UI-06** (v1.4 § Streamlit). Docs/smokes: **DOC-01, TST-01, DOC-02** → **v1.5** Phase 16.

## v1.2 Requirements (superseded for orchestration)

- [x] **AGT-01**, **AGT-02** — superseded by AGT-03–05 / AGT-06–07.

## v1.1 / v1.0

- [x] Baseline QNA, RAG, LIVE, AUTH, API, GC, UI-01–03, RUN-01 — shipped; **QNA-02** superseded by API-05.

## v2 Requirements

Deferred (voice, personalization, Docker, etc.) — unchanged.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Voice-first assistant | Deferred |
| Advanced personalization | Deferred |
| Docker / Compose for v1.x | Local API + Streamlit |
| f1api.dev in answer path | Tavily path |
| **`confidence` in API or UI** | API-05 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| QNA-01 … QNA-03, RAG-*, LIVE-*, AUTH-*, API-01–04 | 1–5 | Complete / superseded |
| GC-*, UI-01–03, RUN-01 | 6–7 | Complete |
| AGT-01–02, SRCH-01–02 | 8 | Complete / superseded |
| AGT-03, AGT-05, SRCH-03, WEB-01, API-05 | 9 | Complete |
| AGT-04 (v1.3 two Tavily) | 9 | **Superseded** → AGT-07 |
| AGT-06, AGT-07, SRCH-04, WEB-02 | 12 | Complete |
| UI-04, UI-05, UI-06 | 13 | Complete |
| RAG-08, RAG-09 | 14 | Complete |
| AGT-08, AGT-09, SRCH-05 | 15 | Pending |
| DOC-01, DOC-02, TST-01 | 16 | Pending |
| TIME-01 | 17 | Pending |
| SCHED-01 | 17 | Pending |
| TOOL-01 | 18 | Pending |

**Coverage (v1.4):** Phases **12–13** complete; Phase **14** complete (**RAG-08/09**); Phases **1–9** complete (subject to v1.4 supersession of AGT-04).

**Coverage (v1.6):** **TIME-01**, **SCHED-01** → Phase **17**; **TOOL-01** → Phase **18**.

---
*Last updated: 2026-03-28 — v1.6 traceability: TIME-01, SCHED-01 (17); TOOL-01 (18); v1.5 rows aligned to phases 14–16*
