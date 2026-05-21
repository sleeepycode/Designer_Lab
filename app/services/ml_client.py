"""
HTTP-клиент ML (контракт ML_module: POST /analyze).

Backend №1 не делает OCR — только передаёт пути/файлы в ML и сохраняет ответ.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from app.core.config import settings


def _base_url() -> str | None:
    base = (settings.ml_service_base_url or '').strip().rstrip('/')
    return base or None


def is_configured() -> bool:
    return _base_url() is not None


def ping() -> dict:
    base = _base_url()
    if not base:
        return {'ok': False, 'error': 'ml_service_base_url не задан'}
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f'{base}/health')
        if response.is_success:
            return {'ok': True, 'status_code': response.status_code}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}
    return {'ok': True, 'note': 'ML доступен по URL (отдельный /health может отсутствовать)'}


def analyze_images(
    image_paths: list[str],
    topic: str,
    document_text: str = '',
) -> dict:
    """POST /analyze — JSON по контракту ML_module/API_CONTRACT.md."""
    base = _base_url()
    if not base:
        raise RuntimeError('Не задан ml_service_base_url в .env')

    url = f'{base}/analyze'
    payload = {
        'document_text': document_text,
        'image_paths': image_paths,
        'topic': topic or 'лабораторной работы',
    }
    with httpx.Client(timeout=120.0) as client:
        response = client.post(url, json=payload)
    if not response.is_success:
        detail = response.text[:500]
        raise RuntimeError(f'ML analyze: {response.status_code} {detail}')
    return response.json()


def analyze_image_file(
    image_path: Path,
    topic: str,
    document_text: str = '',
) -> dict:
    """Анализ одного изображения: один элемент из поля images ответа ML."""
    result = analyze_images([str(image_path.resolve())], topic, document_text)
    images = result.get('images') or []
    if images:
        return images[0]
    errors = result.get('errors') or []
    if errors:
        raise RuntimeError(str(errors[0]))
    raise RuntimeError('ML не вернул данные по изображению')
