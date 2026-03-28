# F1 Assistant — подробная документация

Документ описывает структуру репозитория, способ построения корпуса и индекса, алгоритм поиска, архитектуру агента (LangGraph + GigaChat + Tavily), контракты API и вспомогательные модули. Для быстрого старта и списка переменных окружения см. [README.md](README.md).

---

## 1. Назначение продукта

Асинхронный русскоязычный ассистент по Формуле 1:

1. **Локальный RAG** — векторный поиск по чанкам, собранным из открытых CSV датасета f1db (сезонные сводки на русском).
2. **Синтез ответа** — модель **GigaChat** получает найденные фрагменты и формирует структурированный ответ с ограничением «только по контексту».
3. **Супервизор** — второй вызов GigaChat оценивает, устраивает ли ответ; при отказе — не более **одного** запроса к **Tavily** за ход, опциональная **догрузка одной HTML-страницы**, повторный синтез по веб-сниппетам и снова супервизор.

Внешний REST **f1api.dev** в основном пайплайне чата **не вызывается** (в коде есть утилиты для «живых» сценариев и контракты под live-данные — см. раздел 10).

---

## 2. Дерево проекта и роль файлов

### 2.1. Точки входа

| Путь | Назначение |
|------|------------|
| `api.py` | Запуск **uvicorn** с `reload` только на каталоге `src/`, исключения для `.venv`, `.chroma`, `.git`. |

**Uvicorn вручную** (из корня репозитория), если не используете `api.py`:

```bash
uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload \
  --reload-dir src \
  --reload-exclude .venv --reload-exclude .chroma --reload-exclude .git
```
| `src/main.py` | FastAPI-приложение: `load_dotenv`, роутер чата, глобальный `SessionStore` и `AuthService`, обработчики ошибок. |
| `streamlit_app.py` | UI-оператор: HTTP-клиент к API, опрос статуса, отображение ответа и блока происхождения (provenance). |

### 2.2. Граф агента и веб-поиск

| Путь | Назначение |
|------|------------|
| `src/graph/f1_turn_graph.py` | **LangGraph**: состояние хода, узлы retrieve → RAG-синтез → супервизор → (при необходимости) Tavily → план веба → fetch страницы → веб-синтез → снова супервизор; финализация. |
| `src/graph/tavily_tool.py` | Один вызов Tavily через `langchain_community` + кастомный HTTP wrapper с таймаутом `TAVILY_TIMEOUT`. |
| `src/graph/page_fetch.py` | GET выбранного URL через **httpx**, грубое извлечение текста из HTML (`html.parser`, вырезание script/style). |

### 2.3. LLM и русскоязычная разметка ответа

| Путь | Назначение |
|------|------------|
| `src/answer/gigachat_rag.py` | Все вызовы **GigaChat**: RAG-синтез, веб-синтез, формулировка запроса для Tavily, супервизор accept/reject, план «какую страницу догрузить»; системные промпты и парсинг JSON. |
| `src/answer/russian_qna.py` | Пороги уверенности по score ретривала, сборка `sources_block_ru`, шаблонный structured answer при падении GigaChat; вспомогательные строки для live-сводок. |

### 2.4. Retrieval и индекс

| Путь | Назначение |
|------|------------|
| `src/retrieval/season_summary_corpus.py` | **Единственный источник чанков** для текущего прод-индекса: чтение CSV, генерация русских текстов «обзор сезона» и «гонка + полная классификация». |
| `src/retrieval/index_builder.py` | Подключение к Chroma, `upsert` батчами по 250, опциональная запись markdown-сводок в `scripts/summaries/`. |
| `src/retrieval/embeddings.py` | `SentenceTransformerEmbeddingFunction` для Chroma; модель из `F1_EMBEDDING_MODEL`, иначе локальный `embedding_model/`, иначе Hub `ai-forever/ru-en-RoSBERTa`. |
| `src/retrieval/retriever.py` | Открытие коллекции `f1_historical`, `query` с метаданными, преобразование distance → score, фильтр по году. |
| `src/retrieval/query_normalize.py` | Нормализация строки для API/логов; **извлечение года** для `$and` с метаданными Chroma; **без** словаря сущностей — `canonical_entity_ids` / `entity_tags` всегда пустые. |
| `src/retrieval/evidence.py` | Преобразование сырых hit’ов в `EvidenceItem` (короткий snippet для UI, полный текст для LLM). |
| `src/retrieval/rag_limits.py` | Функция `max_chars_per_rag_chunk()` и переменная `F1_RAG_MAX_CHARS_PER_CHUNK` — **задокументированный** лимит; в текущей версии основной пайплайн GigaChat использует свои константы усечения (см. §5.3). |
| `src/retrieval/document_schema.py` | **Альтернативная** схема: нарратив из **отдельных строк** таблиц (англоязычные шаблоны) + `canonical_entity_id`. Используется для тестов/расширений; **текущий** `build_historical_index` чанки из неё **не строит**. |

### 2.5. API, сессии, авторизация

| Путь | Назначение |
|------|------------|
| `src/api/chat.py` | `POST /start_chat`, `GET /message_status`, `POST /next_message`; нормализация запроса, `asyncio.to_thread(run_f1_turn_sync)`, сборка `details` (evidence, web, provenance). |
| `src/models/api_contracts.py` | Pydantic-модели ответов, `EvidenceItem`, `StructuredRUAnswer`, provenance, web results. |
| `src/sessions/store.py` | In-memory сессии с TTL (по умолчанию 30 мин). |
| `src/auth/service.py` | Проверка кода по allowlist (HMAC compare_digest), интеграция с лимитером. |
| `src/auth/allowlist.py`, `limiter.py`, `dependencies.py`, `errors.py` | Список кодов из `AUTH_ALLOWLIST_CODES`, защита от перебора, `Depends` для `X-Session-Id`. |
| `src/models/auth.py` | `AuthDecision` и коды решений. |

### 2.6. UI и сообщения

| Путь | Назначение |
|------|------------|
| `src/ui/f1_chat_http.py` | HTTP-вызовы API с таймаутом. |
| `src/ui/provenance_display.py` | Markdown для блоков RAG / Web / Fetch / Synthesis в Streamlit. |
| `src/search/messages_ru.py` | Тексты ошибок (в т.ч. `WEB_SEARCH_UNAVAILABLE`). |

### 2.7. Live / календарь (вспомогательно)

| Путь | Назначение |
|------|------------|
| `src/live/gate.py` | Эвристика `requires_live_data` по подстрокам RU/EN. |
| `src/live/messages_ru.py` | Строки для live-сценариев. |

### 2.8. Скрипты и данные

| Путь | Назначение |
|------|------------|
| `scripts/build_f1_season_summaries.py` | CLI: сборка индекса и опциональный `--dump-jsonl` чанков без Chroma. |
| `scripts/summaries/season_YYYY.md` | Артефакты после индексации (удобно для diff/review). |
| `f1db-csv/` | Ожидается у пользователя: набор CSV (см. README). |
| `.chroma/` | Персистентное хранилище Chroma (в `.gitignore`). |
| `certs/*.pem` | Опционально: цепочка НУЦ для verify SSL к GigaChat. |
| `embedding_model/` | Опционально: локальная копия RoSBERTa. |
| `tests/` | Pytest: граф, RAG, API, нормализация запроса, gigachat-моки и т.д. |

---

## 3. Корпус и разбиение на чанки

### 3.1. Источник данных

Используется **ограниченный набор** CSV из f1db (см. комментарии в `index_builder.py` и README):

- `f1db-seasons-driver-standings.csv`, `f1db-seasons-entrants-drivers.csv`, `f1db-seasons-drivers.csv`
- `f1db-drivers.csv`, `f1db-constructors.csv`, `f1db-grands-prix.csv`, `f1db-countries.csv`
- `f1db-races.csv`, `f1db-races-race-results.csv`

### 3.2. Временное окно

- По умолчанию **последние 50 сезонов** относительно **максимального года** в `f1db-races.csv` (`years_span` в `build_historical_index` / `build_season_summary_documents`).

### 3.3. Виды чанков (логика `season_summary_corpus.py`)

1. **`season_overview` (на сезон)**  
   - Одна строка-заголовок: год, число гонщиков, при наличии — пометка чемпиона из `championshipWon`.  
   - **Полная таблица** чемпионата: для каждого участника сезона — строка вида «место / команда — пилот — очки» (источники: зачёт + заявленные пилоты; при отсутствии строки в зачёте — «вне итоговой классификации»).  
   - Хвостовая строка с **поисковыми подсказками** для семантического поиска (сезон, таблица и т.д.).

2. **`grand_prix_race` (на каждую гонку в окне)**  
   - Строка «Итог гонки (победитель)» при наличии P1.  
   - Метаданные этапа: сезон, раунд, название Гран-при, официальное имя, страна.  
   - Блок **идентификаторов для поиска** (grand prix id, год, круг, ключевые слова).  
   - **Полная классификация** всех строк результатов (место, пилот, команда, очки, время/сход).

### 3.4. Идентификаторы чанков

- **`source_id`**: человекочитаемый ключ, например `f1db:season-summary:2023:overview` или `f1db:season-summary:2023:gp:5:monaco-grand-prix`.  
- **`chunk_id`**: **SHA-1** от стабильной строки `dataset=f1db|source_id=...` (детерминированный id для upsert в Chroma).

### 3.5. Метаданные в Chroma

У каждого документа минимум: `dataset`, `table`, `source_id`, `year`, `chunk_kind`; для гонок дополнительно `grand_prix_id` (нижний регистр slug).

---

## 4. Эмбеддинги и индексирование

- Бэкенд: **Chroma** `PersistentClient(path=".chroma")`.  
- Коллекция: **`f1_historical`**.  
- Функция эмбеддингов: **`chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction`** с моделью из `get_embedding_model_name()` (см. §2.4).  
- При **создании** новой коллекции передаётся `embedding_function`; при **чтении** существующей в `retriever` используется `embedding_function=None`, чтобы Chroma применял уже сохранённую конфигурацию векторов и не смешивал модели.

**Важно:** после смены модели эмбеддингов индекс нужно **пересобрать** (старые векторы несовместимы с новыми).

---

## 5. Поиск по чанкам (retrieval)

### 5.1. Тип поиска

Используется **исключительно векторный поиск** (семантический):

- Запрос пользователя передаётся в `collection.query(query_texts=[...], n_results=top_k, where=...)`.  
- Отдельного BM25 / полнотекстового индекса в проекте **нет**.  
- Словарь алиасов сущностей **не используется**; `canonical_entity_ids` в API остаются пустыми.

### 5.2. k ближайших и «расстояние»

- Параметр **`n_results`** в Chroma соответствует **top_k** (в графе для истории: **10**).  
- Chroma возвращает список **`distances`** для каждого результата. В коде ретривера:

```text
score = max(0.0, 1.0 - distance)
```

То есть используется линейное преобразование «чем меньше distance, тем выше score», с отсечением отрицательных значений после преобразования. Конкретная метрика distance задаётся реализацией Chroma для выбранной функции эмбеддингов (для типичных настроек sentence-transformers в экосистеме Chroma это **согласованное с косинусной близостью** пространство; точное имя метрики см. в документации вашей версии Chroma). Порог **`min_score = 0.25`** отсекает слабые совпадения.

Результаты дополнительно **сортируются по убыванию `score`**.

### 5.3. Фильтрация по году

`extract_year_int_from_query` ищет в **исходном** тексте вопроса год в диапазоне **1950–2035** (regex). Если год найден, в `where` добавляется условие `year == "<год>"` (совместно с `dataset == "f1db"` через `$and`).

Если с фильтром по году **нет ни одного** hit’а, выполняется **второй** запрос **без** фильтра по году (fallback), чтобы не терять релевантные чанки при ошибочно угаданном годе.

### 5.4. Что уходит в LLM и в API

- В hit хранится полный текст документа из Chroma, обрезанный до **`MAX_LLM_CHARS_PER_HIT = 16_000`** символов (`retriever.py`) в поле `document_full`.  
- В `evidence.py` в UI/API уходит **`snippet`** до **280** символов; в GigaChat для RAG — **`context_for_llm`**, с усечением в `gigachat_rag._evidence_block_for_llm` до **14_000** символов на фрагмент.

Модуль `rag_limits.max_chars_per_rag_chunk()` (дефолт 8000, env `F1_RAG_MAX_CHARS_PER_CHUNK`) **предусмотрен** для единообразного бюджета, но **не подключён** к `gigachat_synthesize_historical` в текущей версии — фактические лимиты заданы константами в `retriever.py` и `gigachat_rag.py`.

---

## 6. Архитектура агента (LangGraph)

### 6.1. Состояние `F1TurnState` (основные поля)

- Вход: `user_question`, опционально `normalized_query`, пустые `canonical_entity_ids` / `entity_tags`.  
- После retrieve: `retrieval_hits`, `top_score`, `evidence`.  
- Кандидат ответа: `candidate_message`, `candidate_structured`, `synthesis_route`.  
- Супервизор: `supervisor_accept`.  
- Веб: `web_search_rounds` (макс. 1 полноценный заход в Tavily за ход), `tavily_queries`, `web_results`, `last_web_batch`, `tavily_blocked`, `web_plan_best_url`, `web_titles_sufficient`, `fetched_page_excerpt`, `web_provenance_fetch`.

### 6.2. Узлы и рёбра (упрощённо)

```mermaid
flowchart TD
  START([START]) --> retrieve
  retrieve --> agent1_rag
  agent1_rag --> supervisor
  supervisor -->|accept| finalize_accept
  supervisor -->|reject and web_search_rounds >= 1| finalize_fail
  supervisor -->|reject| tavily_search
  tavily_search -->|blocked| finalize_rag_no_tavily
  tavily_search -->|ok| web_plan
  finalize_rag_no_tavily --> finalize_accept
  web_plan -->|titles sufficient or no URL| agent1_web
  web_plan -->|need fetch| fetch_page
  fetch_page --> agent1_web
  agent1_web --> supervisor
  finalize_accept --> END([END])
  finalize_fail --> END
```

- **`retrieve`**: `retrieve_historical_context(user_question, ..., top_k=10, min_score=0.25, year_hint=extract_year_int_from_query(user_question))`, затем `format_evidence`.  
- **`agent1_rag`**: `gigachat_synthesize_historical`; при ошибке GigaChat — шаблонный ответ из `russian_qna` + дисклеймер.  
- **`supervisor`**: `gigachat_supervisor_accept_answer` (JSON `accept`). **Числовой score ретривала здесь не используется** — только текст вопроса и кандидат-ответ.  
- **`tavily_search`**: GigaChat формулирует строку запроса (`gigachat_author_tavily_query`), затем `run_tavily_search_once`.  
- **`finalize_rag_no_tavily`**: Tavily недоступен, но супервизор отклонил RAG — повторный синтез **только по чанкам** с системной подсказкой об отсутствии веба.  
- **`web_plan`**: GigaChat выбирает `best_url` и флаг `titles_sufficient`.  
- **`fetch_page`**: httpx + plain text, до **12_000** символов в state для синтеза.  
- **`agent1_web`**: `gigachat_synthesize_from_web_results` (сниппеты до ~1200 символов на результат + опционально полный текст страницы).  
- После веб-синтеза граф **снова** ведёт в **`supervisor`** (второй шанс принять ответ).  
- **`finalize_fail`**: сообщение `UNABLE_TO_ANSWER_SUPERVISOR_RU` (супервизор отклонил и веб уже был).

`recursion_limit` при `invoke`: **25**.

### 6.3. Маршруты синтеза (`synthesis.route` в ответе API)

Типичные значения: `gigachat_rag`, `gigachat_web`, `template_fallback`, `gigachat_rag_no_web`, `supervisor_gave_up`.

### 6.4. Устаревшие/вспомогательные вызовы в `gigachat_rag.py`

`gigachat_judge_rag_sufficient` — отдельный LLM-судья «достаточен ли контекст»; **текущий скомпилированный граф** после RAG идёт сразу в **супервизора по ответу**, а не в этот judge. Функция остаётся для тестов и возможных альтернативных сборок графа.

---

## 7. GigaChat: роли и форматы

Все вызовы через `GigaChat(**_client_kwargs())` из SDK; учётные данные — стандартные env SDK (в первую очередь **`GIGACHAT_CREDENTIALS`**).

| Функция | Назначение |
|---------|------------|
| `_chat_completion_json` | Ответ строго JSON: `message` + `sections[]`; при невалидном JSON — один repair-раунд в том же чате. |
| `_chat_completion_plain_line` | Одна строка (запрос для Tavily). |
| `gigachat_supervisor_accept_answer` | JSON `{"accept": bool}`. |
| `gigachat_plan_web_use` | JSON `best_url`, `titles_sufficient`. |

Системные промпты зашиты в константах в начале `gigachat_rag.py` (антисгаллюцинации для RAG, ограничение по веб-сниппетам и т.д.).

---

## 8. Tavily

- Инструмент: `TavilySearchResults` с `search_depth="basic"`.  
- Ограничения: `TAVILY_MAX_RESULTS` (по умолчанию 5), HTTP timeout через кастомный `_TavilySearchAPIWrapperWithTimeout`.  
- Без ключа: в графе выставляется `tavily_blocked`, далее ветка `finalize_rag_no_tavily` или при определённых условиях согласованность с `WEB_SEARCH_UNAVAILABLE` (см. тесты и `run_f1_turn_sync`).

---

## 9. HTTP API (контракт поведения)

- **`POST /start_chat`**: тело `StartChatRequest` (код доступа, опционально первый вопрос). Возвращает `session_id`.  
- **`GET /message_status`**: заголовок **`X-Session-Id`**; ответ `status` + `details` при ошибке.  
- **`POST /next_message`**: тот же заголовок; в фоне потока выполняется `run_f1_turn_sync`. Успех: `status: "ready"`, `message`, `details` с `normalized_query`, `evidence`, `structured_answer`, `synthesis`, опционально `web`, `provenance`.

**Provenance** (`details.provenance`): объект с полями `rag` (нормализованный запрос + компактные evidence), при использовании веба — `web` (queries, results, опционально `fetch`), плюс `synthesis` (копия метаданных маршрута).

`EvidenceItem.context_for_llm` в JSON **исключается** (`exclude=True` в Pydantic), чтобы не раздувать ответ.

---

## 10. Прочие модули

- **`src/search/messages_ru.py`**, **`src/live/`** — вспомогательные тексты и эвристики; основной граф F1 хода их может не вызывать.  
- **Тесты** (`tests/`): контракты API, нормализация года, моки GigaChat, сценарии графа (супервизор, Tavily, fetch), RAG-индексация и др.

---

## 11. Зависимости (верхний уровень)

- **FastAPI**, **uvicorn**, **httpx**, **pydantic**, **python-dotenv**  
- **chromadb**, **sentence-transformers**  
- **gigachat** (официальный SDK)  
- **langgraph**, **langchain-core**, **langchain-community** (Tavily)  
- **streamlit** (UI)  
- **pytest** (тесты)

Точные диапазоны версий — в `requirements.txt`.

---

## 12. Связь с кратким README

Установка, команды индексации, запуск `api.py` и Streamlit, таблица переменных окружения — в [README.md](README.md). Этот файл дополняет его **архитектурой и ссылками на код** без дублирования пошаговых команд.
