# Designer Lab — Backend №1 (API / orchestration)

HTTP API для фронта: проекты, задачи, файлы, статусы, вызовы **doc-service** (бэкенд №2) и **ML** (изображения).

**Не входит в эту ветку:** OCR, генерация текста, правка DOCX, применение ГОСТ — это doc-service и ML.

## Запуск

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

`.env` — скопируйте из `.env.example`, укажите **свой пароль** PostgreSQL.

```env
database_url=postgresql+psycopg://postgres:ВАШ_ПАРОЛЬ@localhost:5432/lab_formatter
```

Перед первым запуском (если базы ещё нет):

```bash
python scripts/ensure_postgres_db.py
alembic upgrade head
```

Проверка подключения: `python scripts/check_db.py`

## Архитектура

```text
Фронт → Backend №1
           ├─ картинки (шаг 3) → ML POST /analyze
           └─ DOCX (шаг 4)     → doc-service extract → apply_ml_changes → download PDF/DOCX
```

Подробнее: `docs/DOC_SERVICE_CONTRACT.md`.

## Статусы проекта

`uploaded` → `processing` → `analyzing` (вызов doc-service) → `ready` / `error`

## Хранение

```text
storage/projects/{project_id}/
  input/          # доп. docx
  images/         # png, jpg
  output/         # pdf + docx после process
  metadata.json   # плоский JSON (как в архитектуре проекта)
```

Пример `metadata.json`:

```json
{
  "project_id": "uuid",
  "status": "uploaded",
  "topic": "тема",
  "input_file": "storage/projects/{id}/input/lab.docx",
  "images": ["fig1.png"],
  "output_file": null,
  "output_pdf": null,
  "ml_result": null,
  "errors": [],
  "image_suggestions": []
}
```

## Основные endpoints

| Метод | Путь | Назначение |
|-------|------|------------|
| POST | `/projects/upload` | Создать проект, загрузить DOCX |
| POST | `/projects/{id}/files` | Догрузка (картинки → сразу в ML) |
| GET | `/projects/{id}/suggestions` | Подсказки по картинкам (из ML) |
| POST | `/projects/{id}/process` | Валидация + doc-service + PDF/DOCX |
| GET | `/projects/{id}/download?format=pdf\|docx` | Скачать результат |
| POST | `/tasks/extract` | Превью текста (doc-service extract) |
| POST | `/tasks` | Обработка с загрузкой файла |
| GET | `/health` | Проверка doc-service / ML |

### `POST /projects/{id}/files`

После сохранения `.png`/`.jpg` backend вызывает ML (`ml_service_base_url`) и пишет результат в `metadata.image_suggestions`.

### `POST /projects/{id}/process`

1. Валидация DOCX (минимум текста, без правки файла)  
2. `doc-service`: extract → apply_ml_changes → download PDF + DOCX  
3. Файлы в `output/{task_id}.pdf` и `.docx`

### `POST /projects/{id}/analyze` (опционально)

Превью структуры DOCX через doc-service extract (шаг 2 мастера). Полное оформление — только `process`.

## Проверка

```bash
pytest tests -q
```
