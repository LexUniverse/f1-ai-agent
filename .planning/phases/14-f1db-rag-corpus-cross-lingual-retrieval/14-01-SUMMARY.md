---
phase: 14-f1db-rag-corpus-cross-lingual-retrieval
plan: 01
status: complete
completed: 2026-03-28
---

## Outcome

- **RAG-08:** `CSV_TABLES` whitelist (9 CSV), join `f1db-races` into race-results rows, EN narrative chunks per table, `canonical_entity_id` `race:{grandPrixId}_gp` for results, optional `year` / `grand_prix_id` metadata.
- **Retriever:** `_retrieval_query_variants` — RU query + deterministic EN line when year + `race:*_gp`; merge Chroma hits by `source_id` with max score.
- **Aliases:** RU forms for Monaco → `race:monaco_gp`.
- **RAG-09:** `tests/test_document_schema.py`; `tests/test_rag_grounding.py` — variants, alias, Monaco 2000 / 2021 champion retrieval on schema-built seeds; optional `@pytest.mark.integration_index` + `RUN_F1_INDEX_INTEGRATION=1`.

## Validation

- `pytest tests/test_document_schema.py tests/test_rag_grounding.py -q` — green (integration_index skipped by default).
- Full suite: `pytest -q` — green.

## Notes

- Рекомендуемый порядок локально: `build_historical_index()` затем pytest (см. `14-VALIDATION.md`).
