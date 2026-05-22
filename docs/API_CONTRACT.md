# Контракт API: frontend ↔ backend

Базовый URL: `{VITE_API_BASE_URL}` (по умолчанию `http://127.0.0.1:8000`).

Все запросы с телом файлов — **`multipart/form-data`**, если не указано иное.

Идентификация пользователя: поле или query-параметр **`user_id`** (строка, генерируется на frontend из email).

---

## Используемые endpoints (обязательны для мастера)

### `GET /health`

Проверка доступности (можно использовать для мониторинга; в UI индикатор убран).

**Ответ:** `{ "status": "ok" }` (или как в вашем backend).

---

### `POST /projects/upload`

Загрузка исходного документа.

| Поле | Тип | Обязательно |
|------|-----|-------------|
| `file` | file | да |
| `user_id` | string | нет (рекомендуется) |

**Ответ:**

```json
{
  "project_id": "uuid",
  "status": "uploaded",
  "source_filename": "lab.docx"
}
```

---

### `POST /tasks/extract`

Извлечение абзацев для превью на шаге 2.

| Поле | Тип |
|------|-----|
| `file` | file (.docx) |
| `user_id` | string (опционально) |

**Ответ:**

```json
{
  "paragraphs": ["..."],
  "tables": [[["cell"]]],
  "images": ["path-or-id"]
}
```

---

### `POST /projects/{project_id}/files`

Дополнительные файлы (рисунки).

| Поле | Тип |
|------|-----|
| `file` | file (.png, .jpg) |
| `user_id` | string |

**Ответ (ожидается):** объект с `file_type` (frontend не показывает детали).

---

### `GET /projects/{project_id}/suggestions?user_id=...`

Подсказки по размещению изображений.

**Ответ:**

```json
{
  "project_id": "...",
  "status": "...",
  "suggestions": [
    {
      "id": "string",
      "image_name": "string",
      "image_type": "string",
      "ocr_text": "string",
      "ocr_status": "string",
      "keywords": [],
      "suggested_insertion": "string",
      "caption": "string",
      "applied": false
    }
  ]
}
```

UI показывает: `image_name`, `caption`, `suggested_insertion`.

---

### `POST /projects/{project_id}/suggestions/apply?user_id=...`

Тело JSON:

```json
{ "suggestion_ids": ["id1", "id2"] }
```

**Ответ:** `{ "applied_ids": ["..."] }` (достаточно успешного 200).

---

### `POST /projects/{project_id}/process`

Оформление документа. **Form fields:**

| Поле | Описание |
|------|----------|
| `user_id` | ID пользователя |
| `faculty` | Университет / факультет |
| `department` | Кафедра |
| `student_group` | Группа |
| `lab_title` | Тема работы |
| `lab_number` | Номер работы |
| `student_name` | ФИО студента |
| `reviewer_name` | Преподаватель |
| `discipline` | Дисциплина |

**Ответ:**

```json
{
  "project_id": "...",
  "task_id": "...",
  "status": "...",
  "report": { }
}
```

- Если `report.status === "failed"` — UI показывает ошибку, шаг 5 не открывается.
- Иначе UI запрашивает `GET /tasks/{task_id}/report`.

---

### `GET /tasks/{task_id}/report?user_id=...`

JSON-отчёт для шага 5. Структура свободная; UI проверяет наличие `status`, `message`, `errors[]` для краткого итога.

---

### `GET /projects/{project_id}/download?user_id=...&format=pdf|docx`

Бинарный файл. Параметр **`format`** обязателен для UI: `docx` или `pdf` (без параметра backend по умолчанию отдаёт PDF).

### `POST /auth/register`, `POST /auth/login`, `GET /auth/me`

Регистрация и вход. Ответ: `user_id`, `email`, `access_token`. Дальнейшие запросы к проектам — с тем же `user_id` в form/query; опционально заголовок `Authorization: Bearer <token>` для `/auth/me`.

---

## Зарезервировано в клиенте (мастер сейчас не вызывает)

Можно подключить позже без смены архитектуры:

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/projects/{id}` | Статус проекта |
| POST | `/projects/{id}/analyze` | Запуск анализа |
| GET | `/projects/{id}/analysis` | Результат анализа |
| GET | `/tasks?user_id=&limit=` | История задач |

Функции уже есть в `src/api/client.ts`: `getProject`, `getProjectAnalysis`, `listTasks`.

---

## CORS

Backend должен разрешить origin frontend, например:

- `http://127.0.0.1:3000`
- `http://localhost:3000`

И методы: `GET`, `POST`, `DELETE`, заголовки `Content-Type` (для JSON на apply).

---

## Ошибки

Frontend ожидает:

- HTTP 4xx/5xx с телом FastAPI: `detail` (string или массив с `msg`).
- Сетевые ошибки — сообщение «Не удалось связаться с сервисом…».

При изменении формата ошибок обновите `parseJsonOrThrow` в `client.ts`.

---


