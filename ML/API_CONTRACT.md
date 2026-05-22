# Контракт ML-модуля

## Вход

```json
{
  "document_text": "string",
  "image_paths": ["string"],
  "topic": "string"
}
```

## Выход

```json
{
  "success": true,
  "topic": "string",
  "summary": {
    "status": "ready | needs_review | error",
    "missing_sections_count": 0,
    "images_count": 0,
    "suggestions_count": 0
  },
  "report": {
    "found_sections": [],
    "missing_sections": [],
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
    "ai_provider": "ollama | local",
    "ai_used": true
  }
}
```

## Секции отчёта

Модуль использует технические ключи:

```text
introduction — введение
theory — теоретическая часть
practice — практическая часть
conclusion — заключение
references — список литературы
```

## Типы изображений

```text
graph — график
table — таблица
scheme — схема
formula — формула
unknown — неизвестный тип
```
