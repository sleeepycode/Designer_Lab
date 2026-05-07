<<<<<<< HEAD
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

## Эндпоинт создания

`POST /tasks`

multipart/form-data:
- `file`: исходный DOCX
- `faculty`
- `department`
- `lab_title`
- `lab_number`
- `student_name`
- `reviewer_name`
- `supervisor_name`
- `completion_date`
=======
# Document Processing Service

Микросервис для асинхронной обработки DOCX-файлов лабораторных работ с применением ГОСТ форматирования.

## Архитектура

```
Main Backend (port 8000)
    ↓ HTTP + API Key
Document Service (port 8001)
    ├── FastAPI Server
    ├── Celery Workers (обработка в фоне)
    ├── SQLite DB (отслеживание задач)
    ├── SQLite Broker (очередь Celery)
    └── SQLite Backend (результаты Celery)
```

## Возможности

- **Асинхронная обработка** документов через Celery
- **Отслеживание статуса** задач в БД
- **Callback механизм** для уведомления основного backend'а
- **API аутентификация** через API Key
- **Распределенная обработка** для масштабирования

## Установка и запуск

### 1. Установить зависимости

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Конфигурация (уже готова!)

Celery использует SQLAlchemy вместо Redis - не требуется дополнительная установка!

```bash
# Просто создаются 2 файла БД автоматически:
# - celery_broker.db (очередь задач)
# - celery_results.db (результаты выполнения)
```

### 3. Запустить сервис

**Терминал 1 - FastAPI сервер:**
```bash
python run_server.py
# или
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Терминал 2 - Celery worker:**
```bash
python run_worker.py
# или
celery -A app.core.celery worker --loglevel=info
```

## API Endpoints

### Health Check
```
GET /health
```

### Загрузить документ на обработку
```
POST /api/documents/process
Headers: X-API-Key: <your-api-key>
Content-Type: multipart/form-data

file: <docx file>
user_id: <user_id>
title_page: {"faculty": "...", "department": "...", ...}
callback_url: http://main-backend/callback (опционально)

Response: 202 Accepted
{
  "task_id": "uuid",
  "status": "processing",
  "message": "Документ добавлен в очередь на обработку"
}
```

### Получить статус задачи
```
GET /api/documents/status/{task_id}
Headers: X-API-Key: <your-api-key>

Response: 200 OK
{
  "task_id": "uuid",
  "user_id": "user123",
  "status": "completed|processing|failed|queued",
  "original_filename": "lab.docx",
  "created_at": "2026-04-26T...",
  "updated_at": "2026-04-26T...",
  "errors": [],
  "warnings": [],
  "has_output": true,
  "has_report": true
}
```

### Получить результат обработки
```
GET /api/documents/result/{task_id}
Headers: X-API-Key: <your-api-key>

Response: 200 OK
{
  "task_id": "uuid",
  "user_id": "user123",
  "status": "completed",
  "errors": [],
  "warnings": [],
  "result": {...}
}
```

### Скачать обработанный документ
```
GET /api/documents/output/{task_id}
Headers: X-API-Key: <your-api-key>

Response: 200 OK (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
```

### Скачать отчет об обработке
```
GET /api/documents/report/{task_id}
Headers: X-API-Key: <your-api-key>

Response: 200 OK (application/json)
```

### Удалить задачу и файлы
```
DELETE /api/documents/{task_id}
Headers: X-API-Key: <your-api-key>

Response: 200 OK
{
  "status": "deleted",
  "task_id": "uuid"
}
```

## Callback механизм

После завершения обработки, сервис отправляет POST запрос на `callback_url`:

```json
{
  "task_id": "uuid",
  "user_id": "user123",
  "status": "completed",
  "errors": [],
  "warnings": [],
  "output_url": "http://localhost:8001/api/documents/output/uuid",
  "report_url": "http://localhost:8001/api/documents/report/uuid",
  "result": {...}
}
```

## Конфигурация

Создайте файл `.env` на основе `.env.example`:

```env
# Server
APP_NAME=Document Processing Service
DEBUG=True
PORT=8001

# Celery with SQLAlchemy backend (no Redis needed!)
CELERY_BROKER_URL=sqla+sqlite:///./celery_broker.db
CELERY_RESULT_BACKEND=db+sqlite:///./celery_results.db

# API Authentication
API_KEY=your-super-secret-api-key-change-this

# Main Backend
MAIN_BACKEND_URL=http://localhost:8000
```

## Структура проекта

```
app/
├── api/
│   └── documents.py        # REST API endpoints
├── core/
│   ├── celery.py           # Celery конфигурация
│   ├── config.py           # Settings
│   └── db.py               # SQLAlchemy setup
├── models/
│   └── task.py             # DocumentTask модель
├── schemas/
│   ├── task.py             # Pydantic schemas
│   └── blocks.py           # Структуры документов
├── services/
│   ├── docx_extractor.py   # Извлечение содержимого
│   ├── gost_applier.py     # Применение ГОСТ
│   ├── renderer.py         # Рендеринг документа
│   ├── title_page_generator.py
│   ├── reporting.py        # Генерация отчетов
│   ├── storage.py          # Работа с файлами
│   └── validator.py        # Валидация документов
├── workers/
│   └── tasks.py            # Celery задачи
└── main.py                 # FastAPI приложение

run_server.py              # Запуск сервера
run_worker.py              # Запуск worker'ов
```

## Взаимодействие с Main Backend

**Пример из Python:**

```python
import requests

API_KEY = 'your-secret-api-key-change-this'
DOCUMENT_SERVICE = 'http://localhost:8001'

# 1. Загрузить файл
with open('lab.docx', 'rb') as f:
    files = {'file': f}
    data = {
        'user_id': 'user123',
        'title_page': json.dumps({
            'faculty': 'ФКН',
            'department': 'ИПП',
            'lab_title': 'Лабораторная работа',
            'lab_number': '1',
            'student_group': 'БПМ191',
            'student_name': 'Иван Иванов',
            'reviewer_name': 'Петр Петров',
            'discipline': 'Python'
        }),
        'callback_url': 'http://localhost:8000/callbacks/document-processed'
    }
    headers = {'X-API-Key': API_KEY}
    
    response = requests.post(
        f'{DOCUMENT_SERVICE}/api/documents/process',
        files=files,
        data=data,
        headers=headers
    )
    task = response.json()
    task_id = task['task_id']

# 2. Проверить статус
response = requests.get(
    f'{DOCUMENT_SERVICE}/api/documents/status/{task_id}',
    headers=headers
)
status = response.json()
print(f'Status: {status["status"]}')

# 3. Скачать результат (когда готово)
if status['has_output']:
    response = requests.get(
        f'{DOCUMENT_SERVICE}/api/documents/output/{task_id}',
        headers=headers
    )
    with open('output.docx', 'wb') as f:
        f.write(response.content)
```

## Ограничения MVP

1. Поддерживается только DOCX
2. Сохранение только локально
3. Один worker по умолчанию (можно масштабировать)
4. SQLite для БД (рекомендуется PostgreSQL для production)
5. SQLAlchemy Celery backend (для production рекомендуется RabbitMQ или Redis)


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
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)

## Проверка валидности

- минимум 3000 символов текста;
- минимум 1 таблица или 1 рисунок.
