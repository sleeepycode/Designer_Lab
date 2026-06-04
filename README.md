# Designer Lab — Backend №1

API-оркестратор: проекты, auth, файлы, вызовы **doc-service** и **ML**.  
OCR, ГОСТ и сборка DOCX — **не здесь** (doc-service + ML).

## Структура репозитория (только backend)

```text
app/
  api/          HTTP: auth, projects, tasks
  core/         config, db, security
  models/       PostgreSQL
  schemas/      ответы API
  services/     orchestrator, клиенты doc-service/ML, storage
alembic/        миграции БД
tests/          pytest
docs/           DOC_SERVICE_CONTRACT.md
scripts/        ensure_postgres_db.py, check_db.py
requirements.txt
.env.example    → скопировать в .env
```

**Не в git:** `.env`, `storage/`, `.venv`  
**Не в этой папке:** фронт, doc-service, ML (отдельные репозитории).

## Запуск

```bash
pip install -r requirements.txt
copy .env.example .env
python scripts/ensure_postgres_db.py
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Локально в `.env`: `doc_service_base_url=http://127.0.0.1:8000`, `ml_service_base_url=http://127.0.0.1:8001`, `backend_public_url=http://127.0.0.1:8002`.

Проверка: `GET http://127.0.0.1:8002/health`, `pytest tests -q`.

## Process

```text
POST /projects/{id}/process
  → doc-service extract
  → ML /analyze
  → doc-service apply_ml_changes
  → download DOCX
GET /projects/{id}/download?format=docx
```

Результат: `storage/projects/{id}/output/{task_id}.docx`.

Контракт doc-service: `docs/DOC_SERVICE_CONTRACT.md`.

## Endpoints

| Метод | Путь |
|-------|------|
| POST | `/auth/register`, `/auth/login` |
| POST | `/projects/upload` |
| POST | `/projects/{id}/files` |
| GET | `/projects/{id}/suggestions` |
| POST | `/projects/{id}/process` |
| GET | `/projects/{id}/download?format=docx` |
| POST | `/tasks`, `/tasks/extract` |
| GET | `/health` |
