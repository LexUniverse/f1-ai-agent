# Phase 14: F1DB RAG Corpus & Cross-Lingual Retrieval — Context

**Gathered:** 2026-03-28  
**Status:** Wave **14-02** (replan) — русские сезонные сводки + **ru-en-RoSBERTa**, без алиасов  
**Requirements:** **RAG-08**, **RAG-09** (адаптация: качество через текст чанков и эмбеддинг, не через словарь сущностей)

<domain>

## Phase boundary

**In scope (14-02)**

1. **Узкий набор CSV** (8 файлов): `f1db-seasons-driver-standings`, `f1db-seasons-entrants-drivers`, `f1db-drivers`, `f1db-constructors`, `f1db-grands-prix`, `f1db-countries`, `f1db-races`, `f1db-races-race-results`.
2. **Чанки на русском** за последние **50** сезонов (от макс. года в `f1db-races`):  
   - обзор сезона: число пилотов в итоговой классификации, таблица **команда — пилот — место — очки**, примечание о чемпионе;  
   - на каждый Гран-при: страна, год, официальное имя, **итог гонки** (подиум), строка «идентификаторы для поиска» (en-имена GP, slug, год, раунд).
3. **Эмбеддинги:** `ai-forever/ru-en-RoSBERTa` через Chroma `SentenceTransformerEmbeddingFunction`; **тот же** бэкенд при индексации и при запросе.
4. **Retrieval:** только векторный поиск по **исходному русскому вопросу** пользователя (в графе); **нет** `canonical_entity_id` в `where`; **удалён** `alias_resolver` / `resolve_entities`.
5. **Тесты и прод:** одна модель — `F1_EMBEDDING_MODEL` (дефолт в коде `ai-forever/ru-en-RoSBERTa`); `conftest` делает `setdefault` на тот же дефолт.

**Superseded (14-01)**

- Построчная индексация whitelist из `CSV_TABLES` + EN narrative в `document_schema` для этих таблиц как основной корпус.  
- Двухстрочный запрос (RU + rule-based EN) и расширение `alias_resolver`.

**Out of scope (Phase 15+)**

- Супервизор, веб, два fetch’а (**AGT-08**, **AGT-09**).
- Полный **README_DETAILED.md** (**DOC-02**, фаза 16).

</domain>

<decisions>

## Locked product / planning decisions

- **D-01 (14-02):** Корпус = **сезонные сводки**, не сырые строки всех whitelist-таблиц 14-01.
- **D-02:** Модель эмбеддинга по умолчанию — **`ai-forever/ru-en-RoSBERTa`**; переиндексация при смене модели.
- **D-03:** `chunk_id` стабилен от `source_id` (sha1 от `dataset|source_id`).

</decisions>

<canonical_refs>

## Canonical references

- `.planning/ROADMAP.md` — Phase 14
- `.planning/REQUIREMENTS.md` — RAG-08, RAG-09
- `src/retrieval/season_summary_corpus.py` — `build_season_summary_documents`
- `src/retrieval/index_builder.py` — `build_historical_index`
- `src/retrieval/embeddings.py` — `get_embedding_function`
- `src/retrieval/retriever.py` — `retrieve_historical_context`
- `src/retrieval/query_normalize.py` — `normalize_retrieval_query`
- `src/graph/f1_turn_graph.py` — `_node_retrieve`
- `src/api/chat.py` — `normalize_retrieval_query` → graph
- `scripts/build_f1_season_summaries.py`

</canonical_refs>

<code_context>

## Spot-check данные

- Монако 2000: `f1db-races.csv` `id=653`, `grandPrixId=monaco`; race-results `raceId=653`, позиция 1 → `david-coulthard` (в чанке GP — имена из справочников + русский шаблон).
- Чемпион 2021: строка `f1db-seasons-driver-standings` с `championshipWon=true` → `max-verstappen` в чанке обзора сезона.

</code_context>
