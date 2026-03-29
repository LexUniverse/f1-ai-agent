# F1 Assistant

Асинхронный русскоязычный чат про Формулу 1: **RAG** по локальному индексу (Chroma + CSV f1db), при неудовлетворительном ответе супервизора — **один** запрос **Tavily** за ход и опциональная догрузка страницы; синтез и проверка ответов — **GigaChat**.

**Полная документация** (структура файлов, чанкинг, векторный поиск, LangGraph, промпты, контракты API): [README_DETAILED.md](README_DETAILED.md).

---

## Стек

| Слой | Технологии |
|------|------------|
| API | Python 3.12–3.13 (рекомендуется), FastAPI, uvicorn, Pydantic v2 |
| RAG | Chroma (persistent), sentence-transformers, по умолчанию `ai-forever/ru-en-RoSBERTa` |
| Оркестрация | LangGraph |
| LLM | GigaChat (SDK `gigachat`) |
| Веб-поиск | Tavily через LangChain Community |
| UI | Streamlit, httpx |
| Тесты | pytest |

Зависимости: `requirements.txt`.

---

## Как развернуть у себя

### 1. Окружение

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Скопируйте [`.env.example`](.env.example) в `.env` и задайте минимум:

- **`GIGACHAT_CREDENTIALS`** — для ответов модели ([документация SDK](https://github.com/ai-forever/gigachat)).
- **`TAVILY_API_KEY`** — если нужен веб-поиск при отклонении RAG супервизором ([tavily.com](https://tavily.com)).
- **`AUTH_ALLOWLIST_CODES`** — коды доступа через запятую (для прод-режима API).

Остальные переменные (модель GigaChat, таймауты, `F1_EMBEDDING_MODEL`, `F1_API_BASE_URL` для Streamlit) — в `.env.example` и в [README_DETAILED.md](README_DETAILED.md).

### 2. Индекс RAG

Подготовьте каталог **`f1db-csv/`** с нужными CSV (список файлов — в комментарии в `src/retrieval/index_builder.py`).

```bash
python3 scripts/build_f1_season_summaries.py
```

Индекс создаётся в **`.chroma/`**. После смены модели эмбеддингов пересоберите индекс.

### 3. Запуск

Из **корня репозитория**:

```bash
python api.py
```

API: `http://127.0.0.1:8000` (см. `api.py` при необходимости смены порта).

В другом терминале:

```bash
streamlit run streamlit_app.py
```

В Streamlit укажите код из `AUTH_ALLOWLIST_CODES` и вопрос.

**Совместимость Python:** на 3.14 возможны предупреждения от зависимостей LangChain; для разработки удобнее 3.12/3.13.

**Uvicorn вручную:** ограничьте `--reload-dir` каталогом `src` и исключите `.venv` и `.chroma`, иначе reloader будет лишний раз перезапускать сервер — пример в [README_DETAILED.md](README_DETAILED.md), раздел 2.1.

### 4. Тесты

```bash
pytest
```

Настройки: `pytest.ini`.
