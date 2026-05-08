# API Contract

## Request
```json
{"document_text":"string","image_paths":["string"],"topic":"string"}
```

## Response
```json
{
  "success": true,
  "topic": "string",
  "summary": {"status":"ready | needs_review | error","missing_sections_count":0,"images_count":0,"suggestions_count":0},
  "report": {"found_sections":[],"missing_sections":[],"has_required_structure":false,"generated_sections":[],"bibliography":[]},
  "images": [],
  "content_suggestions": [],
  "errors": [],
  "meta": {"module":"ofor-ml","version":"9.0-api-ready-local-ai","approach":"local-llm-first-safe-fallback","ai_provider":"ollama","ai_used":true}
}
```
