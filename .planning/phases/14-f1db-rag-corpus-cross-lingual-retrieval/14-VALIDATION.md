# Phase 14 — Validation

## Automated (рекомендуемый набор)

```bash
cd /Users/alexshrestha/Documents/pet/AIAgent
python3 -m pytest tests/test_query_normalize.py tests/test_document_schema.py tests/test_rag_indexing.py tests/test_rag_grounding.py -q
```

## Пересборка индекса (prod: RoSBERTa)

Без `F1_CHROMA_DEFAULT_EMBEDDINGS` (иначе векторы не совпадут с тестовым индексом):

```bash
unset F1_CHROMA_DEFAULT_EMBEDDINGS
python3 scripts/build_f1_season_summaries.py
# или:
python3 -c "from src.retrieval.index_builder import build_historical_index; print(build_historical_index())"
```

Затем при необходимости полный прогон тестов в **другом** shell, где для pytest снова не задаётся unset (в проекте `conftest` выставляет default embeddings только на время тестов):

```bash
python3 -m pytest tests/test_rag_grounding.py tests/test_query_normalize.py -q
```

## Дамп чанков (без Chroma)

```bash
python3 scripts/build_f1_season_summaries.py --dump-jsonl /tmp/f1_chunks.jsonl
```

## Manual spot checks (local)

После **`build_historical_index()`** с **RoSBERTa** и перезапуска API:

1. RU: кто победил в Гран-при Монако 2000 — ожидается согласованность с **Култхард** / **Coulthard** в данных.
2. RU: чемпион Ф1 2021 — **Верстаппен** / **Verstappen**.

## Optional full index integration

```bash
unset F1_CHROMA_DEFAULT_EMBEDDINGS
python3 scripts/build_f1_season_summaries.py
export RUN_F1_INDEX_INTEGRATION=1
python3 -m pytest tests/test_rag_grounding.py -q -m integration_index
```
