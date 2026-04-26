# Lab Formatter MVP

Локальный сервис для обработки DOCX-файлов лабораторных работ:
- извлечение содержимого (текст, таблицы, изображения) в JSON-структуру;
- применение ГОСТ-параметров форматирования;
- добавление/замена титульного листа по шаблону;
- валидация исходного DOCX;
- комплексная обработка с титульным листом, ГОСТ и отчетом.

## Изменения

### Новые возможности (версия с новыми модулями)
- **Извлечение содержимого**: Эндпоинт `/tasks/extract` извлекает текст абзацев, таблицы и изображения из DOCX в JSON.
- **Применение ГОСТ**: Эндпоинт `/tasks/apply-gost` применяет ГОСТ-форматирование (шрифт, отступы, поля) к документу.
- **Генерация титульного листа**: Эндпоинт `/tasks/generate-title` добавляет титульный лист к существующему документу или заменяет существующий.
- **Модульная архитектура**: Разделены сервисы для извлечения (`docx_extractor`), применения ГОСТ (`gost_applier`) и генерации титульного листа (`title_page_generator`).
- **Удалены старые модули**: `extractor.py`, `gost_formatter.py`, `title_detector.py` заменены новыми.

### Ограничения MVP

1. Поддерживается только DOCX.
2. Сохранение только локально.
3. Нет очередей и фоновых задач.
4. При извлечении изображения сохраняются локально; при генерации титульного листа существующий титульный лист заменяется.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Перед запуском убедитесь, что PostgreSQL доступен и в `.env` задан корректный `database_url`.

### Миграции БД (Alembic)

- применить миграции: `alembic upgrade head`
- создать новую миграцию: `alembic revision -m "описание_изменения"`

## API

### `POST /tasks` (комплексная обработка)

multipart/form-data:
- `file`: исходный DOCX
- `user_id` (опционально)
- `project_id` (опционально, связывает задачу с проектом)
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

### `POST /tasks/extract` (извлечение содержимого)

multipart/form-data:
- `file`: DOCX для извлечения
- `user_id` (опционально)

Ответ: JSON с ключами `paragraphs`, `tables`, `images`.

### `POST /tasks/apply-gost` (применение ГОСТ)

multipart/form-data:
- `file`: DOCX для форматирования
- `user_id` (опционально)

Ответ: Обработанный DOCX файл.

### `POST /tasks/generate-title` (добавление титульного листа)

multipart/form-data:
- `file`: DOCX для добавления титульного листа
- `department`
- `discipline`
- `lab_number`
- `topic`
- `full_name`
- `group`
- `teacher`
- `user_id` (опционально)

Ответ: DOCX файл с титульным листом (заменяет существующий, если есть).

### `POST /projects/upload` (загрузка исходника проекта)

multipart/form-data:
- `file`: исходный файл (`.docx`, `.pdf`, `.png`, `.jpg`)
- `user_id` (опционально)

Ответ:
- `project_id`
- `status` (`uploaded`)
- `source_filename`

### `POST /projects/{project_id}/files` (дозагрузка файлов в проект)

multipart/form-data:
- `file`: файл (`.docx`, `.pdf`, `.png`, `.jpg`)
- `user_id` (обязателен; можно загружать только в свой проект)

Правило хранения:
- `.docx`, `.pdf` -> `storage/projects/{project_id}/input/`
- `.png`, `.jpg` -> `storage/projects/{project_id}/images/`

Файлы проекта сохраняются в структуре:

```text
storage/projects/{project_id}/
  input/
  images/
  output/
  metadata.json
```

`metadata.json` хранится отдельно от БД и содержит:
- `db_snapshot`: служебный снимок ключевых полей проекта (`project_id`, `status`, `source_path`, `timestamps`, `user_id`);
- `metadata`: данные для работы с проектом (`source_filename`, список файлов, `analysis`, `ml_suggestions`, `processing_errors`).

### `GET /projects/{project_id}` (статус проекта)

Возвращает:
- `project_id`
- `user_id`
- `status` (`uploaded` / `processing` / `analyzing` / `ready` / `error`)
- `source_filename`
- `created_at`, `updated_at`

### `GET /projects/{project_id}/download` (скачать готовый файл проекта)

Query params:
- `user_id` (обязателен; можно скачать только свой результат)

Возвращает последний успешно обработанный DOCX-файл для проекта.
Приоритет источника:
- сначала `storage/projects/{project_id}/output/*.docx`;
- если папка пуста, fallback на `output_path` последней успешной связанной задачи.

### `DELETE /projects/{project_id}` (удалить проект целиком)

Query params:
- `user_id` (обязателен; можно удалить только свой проект)

Удаляет:
- проект из БД,
- связанные задачи проекта,
- папку `storage/projects/{project_id}` со всеми файлами.

### `POST /projects/{project_id}/analyze` (запуск ML-анализа проекта)

Query params:
- `user_id` (обязателен; можно запускать только для своего проекта)

Ответ:
- `project_id`
- `status` (`ready` или `error`)
- `analysis` (результат анализа)

### `GET /projects/{project_id}/analysis` (получить результат ML-анализа)

Query params:
- `user_id` (обязателен; доступ только к своему проекту)

Возвращает:
- `project_id`
- `status`
- `analysis`

### Общие ошибки
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
- `project_id`
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
  - `project_id`
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
