# Doc-service (бэкенд №2) — контракт для backend №1

Swagger: [https://sleeepycode-designer-lab-1dc4.twc1.net/docs](https://sleeepycode-designer-lab-1dc4.twc1.net/docs)

## Пайплайн

```text
Фронт → Backend №1 → doc-service (extract)
                  → doc-service (apply_ml_changes, ML внутри №2)
                  → doc-service (download-pdf + download DOCX)
                  → Backend №1 → Фронт (две кнопки: PDF и DOCX)
```

Backend №1 **не вызывает ML**. В `apply_ml_changes` передаётся `topic` + `title_page`.

## Эндпоинты (реализованы в `app/services/doc_service_client.py`)

| Метод | Путь | Клиент |
|-------|------|--------|
| GET | `/documents/health` | `ping()` |
| POST | `/documents/extract` | `extract_document()` |
| POST | `/documents/apply_ml_changes` | `apply_ml_changes()` |
| GET | `/documents/download/{project_id}` | `download_docx()` |
| GET | `/documents/download-pdf/{project_id}` | `download_pdf()` |
| GET | `/documents/info/{project_id}` | `get_project_info()` |

## POST /documents/apply_ml_changes (тело от backend №1)

```json
{
  "project_id": "uuid-проекта",
  "title_page": {
    "department": "",
    "lab_title": "",
    "lab_number": "",
    "student_group": "",
    "student_name": "",
    "reviewer_name": "",
    "discipline": ""
  },
  "topic": "тема лабораторной"
}
```

Поле `ml_response` **не отправляется** с backend №1 — его формирует doc-service после вызова ML.

## Скачивание с backend №1 (две кнопки на фронте)

| Кнопка | Запрос |
|--------|--------|
| Скачать PDF | `GET /projects/{id}/download?user_id=...&format=pdf` |
| Скачать DOCX | `GET /projects/{id}/download?user_id=...&format=docx` |

Аналогично для задач: `GET /tasks/{id}/download?user_id=...&format=pdf|docx`.

После `process` в отчёте: `outputs.pdf`, `outputs.docx`.

## Postman (проверка doc-service напрямую)

1. **Health** — `GET .../documents/health`
2. **Extract** — `POST .../documents/extract`, form-data: `file`, `project_id`
3. **Apply** — `POST .../documents/apply_ml_changes`, JSON как выше
4. **PDF** — `GET .../documents/download-pdf/{project_id}`

Через backend №1: `POST /projects/{id}/process` → `GET /projects/{id}/download?format=pdf` и `?format=docx`.
