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
- `user_id` (опционально, задел под будущую регистрацию)
- `faculty`
- `department`
- `student_group`
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

Формат ошибки API (единый):
- `code`: машинный код ошибки
- `message`: текст ошибки для человека
- `details`: дополнительная информация (если есть)

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
- `user_id` (опционально, фильтр истории по пользователю)

Ответ:
- `items`: список задач (сначала новые), где у каждой:
  - `task_id`
  - `user_id`
  - `status`
  - `original_filename`
  - `created_at`
  - `has_output`
  - `has_report`

### `GET /tasks/{task_id}/download`

Скачивание итогового DOCX-файла.

Query params:
- `user_id` (обязателен; можно скачать только свой файл)

### `GET /tasks/{task_id}/report`

Скачивание json-отчета обработки.

Query params:
- `user_id` (обязателен; можно скачать только свой отчёт)

### `DELETE /tasks/{task_id}`

Удаление задачи:
- удаляет запись задачи из БД;
- удаляет связанные файлы (input/output/report), если они существуют.

Query params:
- `user_id` (обязателен; можно удалить только свою задачу)

Ответ:
- `task_id`
- `status` (`deleted`)

## Проверка валидности

- минимум 3000 символов текста;
- минимум 1 таблица или 1 рисунок.
