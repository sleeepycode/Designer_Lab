# Document Processing Service

Микросервис для обработки DOCX-файлов лабораторных работ с поддержкой ML-интеграции и ГОСТ форматирования.

## Архитектура

```
Frontend/ML Service
  ↓ HTTP
Document Service (port 8001)
  ├── FastAPI Server
  ├── DOCX Parser
  ├── GOST Formatter
  ├── Title Page Generator
  └── ML Integration
```

## Возможности

- **Извлечение содержимого** DOCX в JSON (параграфы, таблицы, изображения)
- **Применение правок ML** к документу
- **ГОСТ форматирование** (шрифты, отступы, поля)
- **Генерация титульных листов** по шаблону
- **Валидация документов** (объём, наличие таблиц/рисунков)

## Установка и запуск

### 1. Установить зависимости

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Конфигурация

Создайте файл `.env`:

```env
# Server
APP_NAME=Document Processing Service
DEBUG=True
PORT=8001

# ГОСТ параметры
FONT_NAME=Times New Roman
FONT_SIZE_PT=14.0
LINE_SPACING=1.5
FIRST_LINE_INDENT_CM=1.25

MARGIN_LEFT_CM=3.0
MARGIN_RIGHT_CM=1.5
MARGIN_TOP_CM=2.0
MARGIN_BOTTOM_CM=2.0

# Университет
UNIVERSITY_NAME=МИНИСТЕРСТВО ЦИФРОВОГО РАЗВИТИЯ, СВЯЗИ И МАССОВЫХ КОММУНИКАЦИЙ РОССИЙСКОЙ ФЕДЕРАЦИИ...
CITY=Москва
YEAR=2026
```

### 3. Запустить сервис

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## API Endpoints

### Health Check
```
GET /health

Response: 200 OK
{
  "status": "ok"
}
```

---

### 1. Извлечение содержимого DOCX
```
POST /documents/extract
Content-Type: multipart/form-data

Parameters:
- file: DOCX файл (обязательный)
- project_id: ID проекта (опционально, генерируется автоматически)

Response: 200 OK
{
  "project_id": "a1b2c3d4e5f67890",
  "paragraphs": [
    {
      "id": "paragraph_1",
      "text": "Текст параграфа...",
      "source": "original_docx_paragraph",
      "type": "paragraph",
      "position": 0
    }
  ],
  "tables": [...],
  "images": [
    {
      "id": "image_1",
      "path": "storage/projects/{project_id}/media/image1.png",
      "source": "original_docx_image",
      "type": "image",
      "caption": null,
      "position": 0
    }
  ]
}
```

---

### 2. Применение правок ML и сборка документа
```
POST /documents/apply_ml_changes
Content-Type: application/json

Request Body:
{
  "project_id": "a1b2c3d4e5f67890",
  "ml_response": {
    "generated_sections": [
      {
        "section": "introduction",
        "title": "Введение",
        "text": "Текст введения...",
        "source": "ollama"
      },
      {
        "section": "theory",
        "title": "Теоретическая часть",
        "text": "Теоретический текст...",
        "source": "ollama"
      },
      {
        "section": "practice",
        "title": "Практическая часть",
        "text": "Практический текст...",
        "source": "ollama"
      },
      {
        "section": "conclusion",
        "title": "Заключение",
        "text": "Выводы...",
        "source": "ollama"
      }
    ],
    "bibliography": [
      "Источник 1",
      "Источник 2"
    ]
  },
  "title_page": {
    "faculty": "ФКН",
    "department": "ИПП",
    "lab_title": "Название работы",
    "lab_number": "1",
    "student_group": "БПМ191",
    "student_name": "Иванов Иван Иванович",
    "reviewer_name": "Павликов А.Е.",
    "discipline": "Структуры и алгоритмы обработки данных"
  }
}

Response: 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Файл: {project_id}_result.docx
```

---

### 3. Сборка документа из структуры (без ML)
```
POST /documents/assemble
Content-Type: application/json

Request Body:
{
  "paragraphs": ["Текст параграфа 1", "Текст параграфа 2"],
  "tables": [[["ячейка1", "ячейка2"]]],
  "images": [
    {
      "path": "/path/to/image.png",
      "caption": "Рисунок 1 – Описание"
    }
  ]
}

Response: 200 OK
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
```

---

## Форматы данных

### Титульный лист (title_page)

```json
{
  "faculty": "ФКН",
  "department": "ИПП",
  "lab_title": "Название лабораторной работы",
  "lab_number": "1",
  "student_group": "БПМ191",
  "student_name": "Иванов Иван Иванович",
  "reviewer_name": "Павликов А.Е.",
  "discipline": "Структуры и алгоритмы обработки данных"
}
```

### ML ответ (ml_response)

Минимальная структура:
```json
{
  "generated_sections": [
    {
      "section": "introduction",
      "title": "Введение",
      "text": "..."
    }
  ],
  "bibliography": ["Источник 1"]
}
```

Поддерживаемые секции:
- `introduction` — Введение
- `theory` — Теоретическая часть
- `practice` — Практическая часть
- `conclusion` — Заключение

### Блоки изображений

```json
{
  "id": "image_1",
  "path": "storage/projects/{project_id}/media/image1.png",
  "source": "original_docx_image",
  "type": "image",
  "caption": "Рисунок 1 – Описание",
  "position": 0
}
```

---

## Валидация документов

При извлечении документа проверяется:

| Критерий | Требование |
|----------|------------|
| Минимальный объём текста | 3000 символов |
| Наличие таблиц или рисунков | минимум 1 |

---

## Полный пайплайн работы с ML

```
1. POST /documents/extract
   ↓
   Загружаете DOCX → получаете project_id и структуру

2. Отправляете структуру в ML сервис
   ↓
   ML возвращает ml_response с generated_sections

3. POST /documents/apply_ml_changes
   ↓
   Передаёте project_id + ml_response + title_page
   ↓
   Получаете готовый DOCX с:
   - исходным содержимым
   - сгенерированными ML секциями
   - библиографией
   - титульным листом
   - ГОСТ форматированием
```

---

## Структура проекта

```
app/
├── api/
│   └── document_api.py           # Все эндпоинты
├── services/
│   ├── docx_core.py              # Основные функции DOCX
│   ├── document_assembler.py     # ML пайплайн
│   ├── extractor.py              # Извлечение блоков
│   ├── gost_applier.py           # ГОСТ форматирование
│   ├── title_page_generator.py   # Титульные листы
│   ├── captions.py               # Подписи к рисункам/таблицам
│   ├── title_detector.py         # Детекция заголовков
│   └── validator.py              # Валидация
├── core/
│   └── config.py                 # Настройки
├── schemas/
│   └── blocks.py                 # Dataclass'ы блоков
└── main.py                       # FastAPI приложение

storage/
└── projects/
    └── {project_id}/
        ├── {project_id}.docx          # исходный файл
        ├── extract_response.json      # результат извлечения
        ├── merged_structure.json      # объединённая структура (с ML)
        ├── {project_id}_final.docx    # готовый документ
        └── media/                     # извлечённые изображения
```

---


## Переменные окружения (.env)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `APP_NAME` | Название сервиса | Document Processing Service |
| `DEBUG` | Режим отладки | True |
| `PORT` | Порт сервера | 8001 |
| `STORAGE_DIR` | Директория для хранения | storage |
| `FONT_NAME` | Шрифт по ГОСТ | Times New Roman |
| `FONT_SIZE_PT` | Размер шрифта | 14.0 |
| `LINE_SPACING` | Межстрочный интервал | 1.5 |
| `FIRST_LINE_INDENT_CM` | Отступ красной строки | 1.25 |
| `MARGIN_LEFT_CM` | Левое поле | 3.0 |
| `MARGIN_RIGHT_CM` | Правое поле | 1.5 |
| `MARGIN_TOP_CM` | Верхнее поле | 2.0 |
| `MARGIN_BOTTOM_CM` | Нижнее поле | 2.0 |
| `CITY` | Город | Москва |
| `YEAR` | Год | 2026 |

---

## Коды ошибок

| Код | Описание |
|-----|----------|
| `validation_error` | Некорректные входные данные (JSON) |
| `400` | Только .docx файлы разрешены |
| `400` | project_id обязателен |
| `400` | ml_response обязателен |
| `400` | title_page обязателен |
| `500` | Ошибка сборки документа |
| `404` | Файл не найден |

---