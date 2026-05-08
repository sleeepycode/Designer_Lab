import json
from ml.api_adapter import analyze_project_payload
payload = {
    'document_text': 'Введение\n\nПрактическая часть\n\nЗаключение',
    'image_paths': [],
    'topic': 'тестовая тема',
}
print(json.dumps(analyze_project_payload(payload), ensure_ascii=False, indent=2))
