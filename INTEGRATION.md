# Интеграция с Main Backend

## Обзор

Document Processing Service - это независимый микросервис, который обрабатывает DOCX файлы асинхронно. Main Backend может взаимодействовать с ним через REST API.

## Архитектура

```
Main Backend (8000)
     │
     ├─ POST /api/documents/process
     │  └─ Отправить файл на обработку
     │
     ├─ GET /api/documents/status/{task_id}
     │  └─ Проверить статус
     │
     ├─ GET /api/documents/result/{task_id}
     │  └─ Получить результат
     │
     └─ GET /api/documents/output/{task_id}
        └─ Скачать обработанный документ

Document Service (8001)
     │
     ├─ Celery Worker (обработка)
     │  └─ Выполняет задачи асинхронно
     │
     ├─ SQLAlchemy SQLite Broker (очередь)
     │  └─ Хранит задачи в celery_broker.db
     │
     ├─ SQLAlchemy SQLite Backend (результаты)
     │  └─ Хранит результаты в celery_results.db
     │
     └─ SQLite (БД)
        └─ Отслеживает статус задач в lab_formatter.db
```

## Требования

1. ✅ **Ничего дополнительно не требуется!** (используется SQLAlchemy вместо Redis)
2. Document Service должен быть запущен на порту 8001
3. Main Backend должен иметь API Key

## Запуск Document Service

```bash
# Терминал 1: FastAPI сервер
python run_server.py

# Терминал 2: Celery worker
python run_worker.py
```

## Конфигурация

### В Main Backend (.env)

```env
# Document Processing Service
DOCUMENT_SERVICE_URL=http://localhost:8001
DOCUMENT_SERVICE_API_KEY=your-super-secret-api-key-change-this
```

### В Document Service (.env)

```env
API_KEY=your-super-secret-api-key-change-this
MAIN_BACKEND_URL=http://localhost:8000
CELERY_BROKER_URL=sqla+sqlite:///./celery_broker.db
CELERY_RESULT_BACKEND=db+sqlite:///./celery_results.db
```

## Примеры использования

### 1. Загрузить файл на обработку

```python
import requests
import json

DOCUMENT_SERVICE = 'http://localhost:8001'
API_KEY = 'your-super-secret-api-key-change-this'

# Подготовить данные
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
        'callback_url': 'http://localhost:8000/callbacks/document-processed'  # опционально
    }
    headers = {'X-API-Key': API_KEY}
    
    # Отправить запрос
    response = requests.post(
        f'{DOCUMENT_SERVICE}/api/documents/process',
        files=files,
        data=data,
        headers=headers
    )
    
    # Результат
    task = response.json()
    task_id = task['task_id']
    print(f'Task ID: {task_id}')
    print(f'Status: {task["status"]}')
```

**Response (202 Accepted):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Документ добавлен в очередь на обработку"
}
```

### 2. Проверить статус задачи

```python
response = requests.get(
    f'{DOCUMENT_SERVICE}/api/documents/status/{task_id}',
    headers={'X-API-Key': API_KEY}
)

status = response.json()
print(f'Status: {status["status"]}')  # queued, processing, completed, failed
print(f'Errors: {status["errors"]}')
print(f'Warnings: {status["warnings"]}')
```

**Response (200 OK):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "status": "completed",
  "original_filename": "lab.docx",
  "created_at": "2026-04-26T10:00:00",
  "updated_at": "2026-04-26T10:02:15",
  "errors": [],
  "warnings": [],
  "has_output": true,
  "has_report": true
}
```

### 3. Получить результат обработки

```python
response = requests.get(
    f'{DOCUMENT_SERVICE}/api/documents/result/{task_id}',
    headers={'X-API-Key': API_KEY}
)

result = response.json()
print(f'Result: {result["result"]}')
```

### 4. Скачать обработанный документ

```python
response = requests.get(
    f'{DOCUMENT_SERVICE}/api/documents/output/{task_id}',
    headers={'X-API-Key': API_KEY}
)

with open('output.docx', 'wb') as f:
    f.write(response.content)
```

### 5. Скачать отчет об обработке

```python
response = requests.get(
    f'{DOCUMENT_SERVICE}/api/documents/report/{task_id}',
    headers={'X-API-Key': API_KEY}
)

with open('report.json', 'wb') as f:
    f.write(response.content)
```

## Callback механизм

Если передан параметр `callback_url`, Document Service автоматически отправит POST запрос на этот адрес после завершения обработки:

### Создать callback endpoint в Main Backend

```python
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

@app.post('/callbacks/document-processed')
async def document_processed_callback(
    payload: dict,
    x_api_key: str = Header(None)
):
    """Обработать callback от Document Service"""
    
    # Проверить API key
    if x_api_key != settings.DOCUMENT_SERVICE_API_KEY:
        raise HTTPException(status_code=403, detail='Invalid API Key')
    
    task_id = payload['task_id']
    user_id = payload['user_id']
    status = payload['status']
    errors = payload.get('errors', [])
    warnings = payload.get('warnings', [])
    
    # Обновить статус в основной БД
    # ...
    
    # Скачать результаты если нужно
    if status == 'completed':
        output_url = payload.get('output_url')
        report_url = payload.get('report_url')
        
        # Скачать файлы если нужно
        # response = requests.get(output_url, headers={'X-API-Key': API_KEY})
        # ...
    
    return {'status': 'processed'}
```

**Payload callback'а:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "status": "completed",
  "errors": [],
  "warnings": [],
  "output_url": "http://localhost:8001/api/documents/output/550e8400-e29b-41d4-a716-446655440000",
  "report_url": "http://localhost:8001/api/documents/report/550e8400-e29b-41d4-a716-446655440000",
  "result": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "user123",
    "filename": "lab.docx",
    "status": "completed",
    "warnings": [],
    "processing_info": {...}
  }
}
```

## Python SDK (рекомендуется)

```python
# document_service_client.py
import requests
import json

class DocumentServiceClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {'X-API-Key': api_key}
    
    def process_document(self, file_path: str, user_id: str, title_page: dict, callback_url: str = None):
        """Загрузить документ на обработку"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'user_id': user_id,
                'title_page': json.dumps(title_page),
            }
            if callback_url:
                data['callback_url'] = callback_url
            
            response = requests.post(
                f'{self.base_url}/api/documents/process',
                files=files,
                data=data,
                headers=self.headers
            )
        response.raise_for_status()
        return response.json()
    
    def get_status(self, task_id: str):
        """Получить статус задачи"""
        response = requests.get(
            f'{self.base_url}/api/documents/status/{task_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_result(self, task_id: str):
        """Получить результат обработки"""
        response = requests.get(
            f'{self.base_url}/api/documents/result/{task_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def download_output(self, task_id: str, output_path: str):
        """Скачать обработанный документ"""
        response = requests.get(
            f'{self.base_url}/api/documents/output/{task_id}',
            headers=self.headers
        )
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
    
    def download_report(self, task_id: str, report_path: str):
        """Скачать отчет"""
        response = requests.get(
            f'{self.base_url}/api/documents/report/{task_id}',
            headers=self.headers
        )
        response.raise_for_status()
        with open(report_path, 'wb') as f:
            f.write(response.content)
    
    def delete_task(self, task_id: str):
        """Удалить задачу"""
        response = requests.delete(
            f'{self.base_url}/api/documents/{task_id}',
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


# Использование
client = DocumentServiceClient('http://localhost:8001', 'api-key')

# 1. Загрузить файл
task = client.process_document(
    'lab.docx',
    'user123',
    {
        'faculty': 'ФКН',
        'department': 'ИПП',
        'lab_title': 'Лабораторная работа',
        'lab_number': '1',
        'student_group': 'БПМ191',
        'student_name': 'Иван Иванов',
        'reviewer_name': 'Петр Петров',
        'discipline': 'Python'
    }
)
task_id = task['task_id']

# 2. Проверить статус
status = client.get_status(task_id)
print(f'Status: {status["status"]}')

# 3. Скачать результат
if status['status'] == 'completed':
    client.download_output(task_id, 'output.docx')
    client.download_report(task_id, 'report.json')
```

## Обработка ошибок

```python
import requests

try:
    response = requests.get(
        f'{DOCUMENT_SERVICE}/api/documents/status/{task_id}',
        headers=headers,
        timeout=10
    )
    response.raise_for_status()
    status = response.json()
except requests.exceptions.Timeout:
    print('Timeout connecting to Document Service')
except requests.exceptions.ConnectionError:
    print('Document Service is not available')
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print('Invalid API Key')
    elif e.response.status_code == 404:
        print('Task not found')
    else:
        print(f'HTTP Error: {e}')
```

## Polling vs Callback

### Polling (опрос)
Используется когда Main Backend инициирует проверку статуса:
```python
import time

task = client.process_document(...)
task_id = task['task_id']

# Опрашивать пока не завершится
while True:
    status = client.get_status(task_id)
    if status['status'] == 'completed':
        print('Done!')
        break
    elif status['status'] == 'failed':
        print(f'Error: {status["errors"]}')
        break
    time.sleep(2)  # Проверять каждые 2 секунды
```

### Callback (уведомление)
Document Service сам отправляет результат когда готово:
```python
task = client.process_document(
    ...,
    callback_url='http://localhost:8000/callbacks/document-processed'
)
# Ждем callback на эндпоинт
```

## Масштабирование

Для обработки большего количества документов одновременно:

```bash
# Запустить несколько worker'ов
python run_worker.py  # Worker 1
python run_worker.py  # Worker 2 (в другом терминале)
python run_worker.py  # Worker 3 (в другом терминале)
```

Или используя Linux/Mac:
```bash
celery -A app.core.celery worker --loglevel=info --concurrency=10
```

## Мониторинг

```bash
# Просмотреть очередь задач
celery -A app.core.celery inspect active

# Просмотреть завершенные задачи
celery -A app.core.celery inspect registered

# Просмотреть статистику worker'а
celery -A app.core.celery inspect stats
```

## Troubleshooting

### Celery tasks не выполняются
```bash
# Убедиться что worker запущен
python run_worker.py

# Проверить логи
celery -A app.core.celery worker --loglevel=debug
```

### БД файлы не создаются
```bash
# Убедиться что у приложения есть права на запись в текущей директории
# Файлы создадутся автоматически:
# - celery_broker.db
# - celery_results.db
# - lab_formatter.db
```

### Callback не отправляется
```bash
# Проверить что callback_url доступен
curl -X POST http://localhost:8000/callbacks/document-processed \
  -H "X-API-Key: api-key" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "test"}'
```

## Security

1. **Менять API Key** в production
2. **Использовать HTTPS** для callback'ов
3. **Ограничить доступ** через firewall
4. **Использовать разные API Key'и** для разных сервисов
5. **Логировать** все запросы
