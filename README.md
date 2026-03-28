# F1 Assistant

Асинхронный чат про Формулу 1 на русском: **RAG** по локальному индексу (Chroma + CSV f1db), при слабом или пустом контексте — **веб-поиск Tavily** (через LangChain). Ответы собирает **GigaChat** (судья по достаточности RAG, формулировка поискового запроса, синтез по чанкам и по сниппетам из веба). **Отдельный REST API Formula 1 (f1api.dev) в пайплайне не используется.**

Docker для локального запуска **не обязателен**.

---

## Где что в коде

| Что | Файл |
|-----|------|
| **LangGraph** (узлы: retrieve → sufficiency → RAG или Tavily → синтез) | `src/graph/f1_turn_graph.py` |
| **Tavily** (LangChain Community, один запрос за ход) | `src/graph/tavily_tool.py` |
| **Вызовы GigaChat** (чат-комплишены) | `src/answer/gigachat_rag.py` |
| **HTTP API** (`/start_chat`, `/message_status`, `/next_message`), запуск графа в потоке | `src/api/chat.py` |
| **Точка входа сервера** | `api.py`, `src/main.py` |
| **Нормализация текста запроса** (без словаря алиасов; RAG только по вектору) | `src/retrieval/query_normalize.py` |
| **Русские сезонные сводки для индекса** (последние N лет из нескольких CSV) | `src/retrieval/season_summary_corpus.py` |
| **Эмбеддинги Chroma** (по умолчанию `ai-forever/ru-en-RoSBERTa`) | `src/retrieval/embeddings.py` |
| **Поиск по Chroma** | `src/retrieval/retriever.py` |
| **Streamlit-клиент** | `streamlit_app.py` |

Цепочка запроса: `next_message` → `normalize_retrieval_query` → `run_f1_turn_sync` → в графе векторный поиск по **исходному русскому вопросу** (та же модель эмбеддинга, что при индексации), затем при необходимости `gigachat_rag.py` и `tavily_tool.py`.

---

## Почему в репозитории нет строки `GIGACHAT_CREDENTIALS`

Ключ **нужен**, но приложение **не читает** переменную само: клиент **`gigachat`** при создании `GigaChat()` подхватывает стандартные переменные окружения из процесса (в первую очередь **`GIGACHAT_CREDENTIALS`** — Base64 для Basic-авторизации из личного кабинета). См. [документацию SDK](https://github.com/ai-forever/gigachat).

Использование в коде: все вызовы идут через `GigaChat(**_client_kwargs())` в `src/answer/gigachat_rag.py` (`_chat_completion_json`, `_chat_completion_plain_line` и т.д.).

---

## RAG без алиасов

Статический **`alias_resolver`** убран. Индекс строится из **русскоязычных сезонных сводок** (число пилотов, таблица «команда — пилот — место — очки», отдельный чанк на каждый Гран-при с подиумом и поисковыми подсказками). Запрос пользователя эмбеддится моделью **`ai-forever/ru-en-RoSBERTa`**. При слабом совпадении по-прежнему может сработать **Tavily**, если задан `TAVILY_API_KEY`.

---

## Переменные окружения

Скопируйте `.env.example` → `.env` и заполните.

| Переменная | Обязательно | Назначение | Где взять |
|------------|-------------|------------|-----------|
| **`GIGACHAT_CREDENTIALS`** | Да, для реальных ответов LLM | Авторизация GigaChat (читает SDK) | [GigaChat API / кабинет](https://developers.sber.ru/portal/products/gigachat-api), см. [gigachat-python](https://github.com/ai-forever/gigachat) |
| **`TAVILY_API_KEY`** | Да, если нужен веб-поиск при слабом RAG | Поиск Tavily | [tavily.com](https://tavily.com) — API key в дашборде |
| **`AUTH_ALLOWLIST_CODES`** | Да для прод-режима | Коды доступа через запятую | Задаёте сами |
| **`F1_API_BASE_URL`** | Нет | Базовый URL API для Streamlit (по умолчанию `http://127.0.0.1:8000`) | Локально не менять |
| **`GIGACHAT_MODEL`** | Нет | Имя модели (по умолчанию `GigaChat`) | Документация GigaChat |
| **`GIGACHAT_TIMEOUT`**, **`GIGACHAT_MAX_RETRIES`**, **`GIGACHAT_VERIFY_SSL_CERTS`** | Нет | Тонкая настройка клиента | См. `.env.example` |
| **`TAVILY_TIMEOUT`**, **`TAVILY_MAX_RESULTS`** | Нет | Таймаут и число результатов Tavily | `src/graph/tavily_tool.py` |
| **`F1_EMBEDDING_MODEL`** | Нет | Имя модели для Chroma (`sentence-transformers`) | По умолчанию `ai-forever/ru-en-RoSBERTa` |
| **`F1_CHROMA_DEFAULT_EMBEDDINGS`** | Нет | Если `1` — встроенный эмбеддер Chroma (только для отладки; **не совпадает** с прод-индексом) | Тесты выставляют сами |
| **`F1_LOG_AGENT_TRACE`** | Нет | Если `1` — в **stderr** трассировка retrieve / agent1_rag / supervisor / tavily / web (короткие превью) | Отладка промптов |
| **`F1_LOG_SUPERVISOR_DECISIONS`** | Нет | Логи супервизора через `logging` | См. `gigachat_rag.py` |

Без **`TAVILY_API_KEY`** при нехватке RAG ответ завершится ошибкой **`WEB_SEARCH_UNAVAILABLE`** (см. `src/search/messages_ru.py`).

---

## Установка и индекс RAG

### Версия Python

Рекомендуется **3.12 или 3.13**. На **3.14** возможны предупреждения вида `Pydantic V1 … isn't compatible with Python 3.14` из зависимостей LangChain — это известное несоответствие до обновления upstream; для спокойной разработки лучше venv на 3.12/3.13.

### Виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Запуск API:

- **Предпочтительно:** `python api.py` — смотрит только каталог **`src/`** и не должен перезагружаться из‑за правок в **`.venv`** (chromadb и др. тянут тяжёлые пакеты с `.py` в site-packages).
- Если запускаете **uvicorn вручную**, обязательно ограничьте каталоги, иначе reloader увидит `.venv/.../*.py` и будет крутить перезапуск по кругу:

  ```bash
  uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload \
    --reload-dir src \
    --reload-exclude .venv --reload-exclude .chroma --reload-exclude .git
  ```

  (`--reload-exclude` можно повторять; пути заданы относительно текущей директории — запускайте из корня репозитория.)

### Сборка Chroma из CSV (сезонные сводки)

Иначе retrieval не найдёт чанки (до GigaChat/Tavily дойдёт только «пустой» контекст).

1. Подготовьте **`f1db-csv/`** с файлами, из которых собирается сводка (минимальный набор):  
   `f1db-seasons-driver-standings.csv`, `f1db-seasons-entrants-drivers.csv`, `f1db-drivers.csv`, `f1db-constructors.csv`, `f1db-grands-prix.csv`, `f1db-countries.csv`, `f1db-races.csv`, `f1db-races-race-results.csv`.
2. Соберите индекс (последние **50** сезонов от максимального года в CSV; эмбеддинги **ru-en-RoSBERTa**, первый запуск скачает веса):

```bash
python3 scripts/build_f1_season_summaries.py
# или:
python3 -c "from src.retrieval.index_builder import build_historical_index; print(build_historical_index())"
```

Опционально посмотреть чанки без Chroma:  
`python3 scripts/build_f1_season_summaries.py --dump-jsonl /tmp/f1_chunks.jsonl`

Индекс пишется в **`.chroma/`**; переиндексация **обязательна** после смены модели эмбеддингов.

---

## Запуск

Из **корня репозитория**:

1. **`python api.py`** — API на `127.0.0.1:8000` (или см. `api.py`).
2. В другом терминале: **`streamlit run streamlit_app.py`**.

В Streamlit укажите код из **`AUTH_ALLOWLIST_CODES`** и вопрос.

---

## Тесты

```bash
pytest
```

Настройки см. `pytest.ini`. Отдельные smoke-тесты с реальными GigaChat/Tavily (по плану майлстоуна) могут быть добавлены позже с маркером `integration`.
