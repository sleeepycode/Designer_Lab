# Lab Formatter MVP

Локальный сервис для создания нового DOCX-файла лабораторной работы:
- добавляет титульный лист по фиксированному шаблону;
- валидирует исходный DOCX;
- приводит текст к жестко заданному ГОСТ-профилю;
- добавляет подписи таблиц и рисунков.

## Ограничения MVP

1. Поддерживается только DOCX.
2. Сохранение только локально.
3. Нет очередей и фоновых задач.
4. При создании нового документа встроенные изображения из исходного файла не копируются побайтно; вместо этого ставится маркер `[Изображение из исходного документа]` и подпись. Это ограничение `python-docx` при высокоуровневом копировании.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## API

### `POST /tasks`

multipart/form-data:
- `file`: исходный DOCX
- `faculty`
- `department`
- `lab_title`
- `lab_number`
- `student_name`
- `reviewer_name`
- `discipline`

Ответ:
- `task_id`
- `status` (`completed` или `failed`)
- `report` (json-отчет о проверке/обработке)

Ошибки:
- `400 Поддерживается только формат DOCX.`
- `400 Входной файл пустой.`
- `400 Не удалось прочитать DOCX. Проверьте, что файл не поврежден.`

### `GET /tasks/{task_id}`

Возвращает статус задачи:
- `task_id`
- `status` (`created` / `completed` / `failed`)
- `errors`, `warnings`
- `has_output`, `has_report`

### `GET /tasks`

История задач для вкладки на фронте.

Query params:
- `limit` (по умолчанию `20`, максимум `100`)

Ответ:
- `items`: список задач (сначала новые), где у каждой:
  - `task_id`
  - `status`
  - `original_filename`
  - `created_at`
  - `has_output`
  - `has_report`

### `GET /tasks/{task_id}/download`

Скачивание итогового DOCX-файла.

### `GET /tasks/{task_id}/report`

Скачивание json-отчета обработки.

## Проверка валидности

- минимум 3000 символов текста;
- минимум 1 таблица или 1 рисунок.
