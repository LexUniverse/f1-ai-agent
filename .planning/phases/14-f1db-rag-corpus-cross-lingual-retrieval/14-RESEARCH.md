# Phase 14 — Research notes

**Date:** 2026-03-28  
**Scope:** Chroma ingest, cross-lingual retrieval без обязательного билингва в чанках

## Findings

1. **Chroma** (`collection.query(query_texts=[...], where=...)`) принимает **несколько** текстов запроса в одном вызове; расстояния/документы возвращаются по каждому. Альтернатива — два вызова и merge по `source_id` с лучшим score. Для фазы достаточно **≤2** строк на ход (**D-02**).

2. **Join на этапе индекса** предпочтительнее join в runtime: `f1db-races-race-results` не содержит `grandPrixId`; один проход по `f1db-races.csv` в память (`dict[race_id] → {grandPrixId, year, officialName, …}`) позволяет обогатить каждую строку результата для **текста чанка** и **`canonical_entity_id`** (`race:{gp}_gp` в том же виде, что в `alias_resolver`).

3. **Натуральный английский шаблон** для строки результата гонки (пример):  
   `Race result: {officialName or GP name}, season {year}, finishing position {n}: driver {driverId}, constructor {constructorId}, points {points}.`  
   Для справочников — одно-два предложения с полными именами из CSV.

4. **RU запросы:** эмбеддинги GigaChat/Chroma могут слабо матчить русский на английский текст. Минимальная связка без LLM: **regex год** из нормализованного запроса + **известный GP** из алиаса → вторая строка запроса на английском. LLM-expansion — запасной путь с моками в тестах.

5. **Стабильность тестов:** полная пересборка `.chroma` в CI может быть тяжёлой; **RAG-09** может использовать либо (a) маркированный интеграционный тест с локальным `f1db-csv`, либо (b) seed коллекции с **тремя** документами нового формата + проверка `retrieve_historical_context` с реальным эмбеддером и ослабленным `min_score`, либо (c) оба: быстрый unit на merge логике + один opt-in интеграционный.

## Claude's discretion

- Точные шаблоны предложений по каждой таблице whitelist.
- Использовать ли один `query` с двумя `query_texts` или два вызова `query`.
- Добавлять ли в фазе 14 вызов GigaChat для expansion или ограничиться rule-based.
