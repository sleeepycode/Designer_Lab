# Doc-service (бэкенд №2) — контракт для backend №1

Swagger: [https://sleeepycode-designer-lab-1dc4.twc1.net/docs](https://sleeepycode-designer-lab-1dc4.twc1.net/docs)

## Пайплайн (backend №1)

```text
Фронт → Backend №1 → doc-service extract
                  → ML /analyze (backend №1)
                  → doc-service apply_ml_changes (ml_response + uploaded_images)
                  → doc-service download DOCX
                  → Backend №1 → Фронт (одна кнопка: DOCX)
```

PDF **не используется** — пользователю отдаётся только DOCX.

## Эндпоинты (`app/services/doc_service_client.py`)

| Метод | Путь | Клиент |
|-------|------|--------|
| GET | `/documents/health` | `ping()` |
| POST | `/documents/extract` | `extract_document()` |
| POST | `/documents/apply_ml_changes` | `apply_ml_changes()` |
| GET | `/documents/download/{project_id}` | `download_docx()` |
| GET | `/documents/info/{project_id}` | `get_project_info()` |

## POST /documents/apply_ml_changes

```json
{
  "project_id": "uuid",
  "ml_response": { },
  "uploaded_images": [ ],
  "title_page": { "faculty": "", "department": "", "lab_title": "", "lab_number": "", "student_group": "", "student_name": "", "reviewer_name": "", "discipline": "" },
  "topic": "тема"
}
```

Локальный doc-service требует `ml_response` — его собирает backend №1 после `POST /analyze` на ML.

## Скачивание с backend №1

| Действие | Запрос |
|----------|--------|
| Скачать результат | `GET /projects/{id}/download?user_id=...&format=docx` (по умолчанию) |

`format=pdf` → **400** (отключено).

После `process` в отчёте: `outputs.docx`.
