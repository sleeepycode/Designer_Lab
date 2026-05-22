from typing import Any
from ml.config import MODULE_NAME, MODULE_VERSION, AI_PROVIDER

def build_project_response(topic: str, report: dict, images: list[dict], content_suggestions: list[dict], errors: list[str] | None = None, ai_used: bool = False) -> dict[str, Any]:
    errors = errors or []
    status = 'error' if errors else ('needs_review' if report.get('missing_sections') or content_suggestions else 'ready')
    return {'success': not bool(errors), 'topic': topic, 'summary': {'status': status, 'missing_sections_count': len(report.get('missing_sections', [])), 'images_count': len(images), 'suggestions_count': len(content_suggestions)}, 'report': report, 'images': images, 'content_suggestions': content_suggestions, 'errors': errors, 'meta': {'module': MODULE_NAME, 'version': MODULE_VERSION, 'approach': 'local-llm-first-safe-fallback', 'ai_provider': AI_PROVIDER, 'ai_used': ai_used}}

def build_image_error(image_path: str, error: str) -> dict:
    return {'path': image_path, 'type': 'unknown', 'ocr_text': '', 'keywords': [], 'caption': 'Рисунок — Иллюстрация к отчёту', 'number': None, 'numbering_type': 'figure', 'placement': {'paragraph_index': 0, 'score': 0.0, 'reason': 'Не удалось проанализировать изображение'}, 'alternatives': [], 'confidence': 0.0, 'error': error}
