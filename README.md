# Designer Lab — Backend №1

API-оркестратор: проекты, auth, файлы, вызовы **doc-service** и **ML**.

## База данных: SQLite (по умолчанию)

Файл `lab_formatter.db` в корне проекта — **отдельный сервер PostgreSQL не нужен**.

Таблицы (`users`, `projects`, `document_tasks`) создаются автоматически при старте (`init_db`).

## Запуск

```bash
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Проверка БД: `python scripts/check_db.py`  
Тесты: `pytest tests -q`

## Структура

```text
app/              ← код backend
alembic/          ← миграции (для PostgreSQL на сервере; локально SQLite — init_db)
requirements.txt
.env.example
```

## `.env`

```env
database_url=sqlite:///./lab_formatter.db
backend_public_url=http://127.0.0.1:8002
doc_service_base_url=http://127.0.0.1:8000
ml_service_base_url=http://127.0.0.1:8001
```

## Process

`POST /projects/{id}/process` → extract → ML → apply_ml_changes → DOCX  
`GET /projects/{id}/download?format=docx`

Контракт doc-service: `docs/DOC_SERVICE_CONTRACT.md`.

## PostgreSQL (опционально, прод)

В `.env`: `database_url=postgresql+psycopg://...`, `pip install psycopg[binary]`, `alembic upgrade head`.
