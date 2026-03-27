# F1 Assistant

## Local run (v1.1)

Docker **не** требуется для v1.1.

1. Установите зависимости: `pip install -r requirements.txt`
2. Запустите API одним из способов:
   - `python api.py` (uvicorn с перезагрузкой на `127.0.0.1:8000`)
   - `uvicorn src.main:app --reload --host 127.0.0.1 --port 8000`
3. В другом терминале запустите интерфейс: `streamlit run streamlit_app.py`

Скопируйте `.env.example` в `.env` и задайте ключи (в т.ч. допустимые коды доступа для тестов).
