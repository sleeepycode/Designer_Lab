# ML-модуль анализа отчётов

Модуль предназначен для проекта «Оформлятор». Он принимает текст отчёта, список изображений и тему работы, после чего возвращает структурированный JSON для backend.

## Что делает модуль

Модуль выполняет несколько задач:

1. Анализирует структуру отчёта.
2. Определяет найденные и отсутствующие разделы.
3. Генерирует недостающие разделы через Ollama или fallback-логику.
4. Формирует список литературы.
5. Обрабатывает изображения через OCR.
6. Классифицирует изображения: `graph`, `table`, `scheme`, `formula`, `unknown`.
7. Генерирует подписи к изображениям.
8. Предлагает место вставки изображения в документ.
9. Возвращает результат в JSON-формате для backend.

## Основная функция

```python
from ml.service import analyze_project

result = analyze_project(
    document_text=document_text,
    image_paths=image_paths,
    topic=topic,
)
```

Параметры:

```python
document_text: str
```

Текст документа, который backend получил из DOCX/PDF.

```python
image_paths: list[str]
```

Список путей к изображениям. В этот список можно передавать и изображения, загруженные пользователем через back1, и изображения, извлечённые из документа через back2.

```python
topic: str
```

Тема отчёта или лабораторной работы.

## Пример входных данных

```json
{
  "document_text": "Введение\nЦель работы — изучить алгоритмы сортировки...",
  "image_paths": [
    "storage/projects/123/images/user_graph.png",
    "storage/projects/123/images/docx_scheme.png"
  ],
  "topic": "Алгоритмы сортировки"
}
```

## Пример вызова

```python
from ml.service import analyze_project

payload = {
    "document_text": "Введение\nЦель работы — изучить алгоритмы сортировки...",
    "image_paths": [
        "storage/projects/123/images/user_graph.png",
        "storage/projects/123/images/docx_scheme.png",
    ],
    "topic": "Алгоритмы сортировки",
}

result = analyze_project(
    document_text=payload["document_text"],
    image_paths=payload["image_paths"],
    topic=payload["topic"],
)

print(result)
```

## Пример ответа

```json
{
  "success": true,
  "topic": "Алгоритмы сортировки",
  "summary": {
    "status": "needs_review",
    "missing_sections_count": 2,
    "images_count": 2,
    "suggestions_count": 2
  },
  "report": {
    "found_sections": ["introduction", "practice"],
    "missing_sections": ["theory", "conclusion", "references"],
    "has_required_structure": false,
    "generated_sections": [],
    "bibliography": []
  },
  "images": [],
  "content_suggestions": [],
  "errors": [],
  "meta": {
    "module": "ofor-ml",
    "version": "9.0-api-ready-local-ai",
    "approach": "local-llm-first-safe-fallback",
    "ai_provider": "ollama",
    "ai_used": true
  }
}
```

## Статусы ответа

```text
ready
```

Документ выглядит полным, критических замечаний нет.

```text
needs_review
```

Найдены отсутствующие разделы или предложения по доработке.

```text
error
```

Во время обработки возникли ошибки, например пустой текст документа или несуществующий путь к изображению.

## Установка

Рекомендуется Python 3.10–3.12. Для OCR лучше не использовать Python 3.14, потому что часть библиотек может быть нестабильна или недоступна.

Создать виртуальное окружение:

```bash
py -3.11 -m venv .venv
```

Активировать окружение в PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Если PowerShell блокирует запуск скриптов:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.venv\Scripts\Activate.ps1
```

Обновить pip и установить зависимости:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Настройка `.env`

В корне проекта нужно создать файл `.env`. Можно скопировать `.env.example`:

```bash
copy .env.example .env
```

Для работы с Ollama:

```env
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

Для работы без LLM можно указать:

```env
AI_PROVIDER=local
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
```

В режиме `local` модуль использует fallback-логику. Это полезно, если Ollama не запущена.

## Настройка Ollama

Установить Ollama с официального сайта.

Загрузить модель:

```bash
ollama pull llama3.2:3b
```

Для слабого ПК можно использовать более лёгкую модель:

```bash
ollama pull qwen2.5:1.5b
```

Запустить Ollama:

```bash
ollama serve
```

Если появляется ошибка вида:

```text
bind: Only one usage of each socket address is normally permitted
```

значит Ollama уже запущена, второй раз запускать её не нужно.

## Интеграция с backend

Backend должен передать в ML-модуль:

```json
{
  "document_text": "текст документа",
  "image_paths": ["путь_к_изображению_1", "путь_к_изображению_2"],
  "topic": "тема отчёта"
}
```

Для текущей версии неважно, откуда пришла картинка:

```text
back1: изображения, загруженные пользователем
back2: изображения, извлечённые из DOCX/PDF
```

Оба типа изображений можно передавать в общий список `image_paths`.

В будущем можно расширить контракт и передавать источник изображения явно:

```json
{
  "path": "storage/projects/123/images/graph.png",
  "source": "back1_user_upload"
}
```

Но для текущей версии это не обязательно.

## Что backend получает от ML

Backend получает JSON, где есть:

- `success` — успешность обработки;
- `summary` — краткий статус;
- `report` — анализ структуры отчёта;
- `images` — анализ изображений;
- `content_suggestions` — предложения по доработке;
- `errors` — ошибки;
- `meta` — служебная информация о модуле.

## Важные файлы

```text
ml/service.py
```

Главная точка входа. Здесь находится функция `analyze_project`.

```text
ml/ai_report.py
```

Анализ структуры отчёта: введение, теория, практика, заключение, список литературы.

```text
ml/ai_generation.py
```

Генерация недостающих разделов и списка литературы.

```text
ml/image_analyzer.py
```

Общий пайплайн анализа изображения.

```text
ml/ocr.py
```

OCR через PaddleOCR и EasyOCR с fallback-логикой.

```text
ml/image_classifier.py
```

Классификация изображения по OCR-тексту.

```text
ml/placement_suggester.py
```

Подбор места вставки изображения в документ.

```text
ml/numbering_generator.py
```

Нумерация рисунков, таблиц и формул.

```text
ml/ollama_client.py
```

Клиент для обращения к локальной Ollama.

## Fallback-логика

Модуль не должен падать, если Ollama или OCR временно недоступны.

Основная схема:

```text
Ollama доступна → используется генерация через LLM
Ollama недоступна → используется fallback-генерация
PaddleOCR работает → используется PaddleOCR
PaddleOCR падает → используется EasyOCR
EasyOCR тоже падает → возвращается пустой OCR-текст и ошибка в JSON
```

## Что можно говорить на защите

ML-модуль принимает текст отчёта, изображения и тему работы. После этого он анализирует структуру документа, определяет отсутствующие разделы, генерирует недостающий контент, обрабатывает изображения через OCR, классифицирует их, создаёт подписи и предлагает места вставки. Результат возвращается в виде JSON, который backend может использовать для дальнейшего форматирования и сборки итогового DOCX/PDF.
