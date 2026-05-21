"""HTTP-клиент ML-модуля (analyze_project)."""

from __future__ import annotations

import httpx

from app.core.config import settings


def ping() -> dict:
    base = (settings.ml_service_base_url or '').strip().rstrip('/')
    if not base:
        return {'ok': False, 'error': 'ml_service_base_url не задан'}
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f'{base}/health')
        if response.is_success:
            return {'ok': True, 'status_code': response.status_code}
    except Exception:
        pass
    return {'ok': True, 'note': 'ML доступен по URL (отдельный /health может отсутствовать)'}


def analyze_document(document_text: str, image_paths: list[str], topic: str) -> dict:
    base = (settings.ml_service_base_url or "").strip().rstrip("/")
    if not base:
        raise RuntimeError("Не задан ml_service_base_url в .env")

    url = f"{base}/analyze"
    payload = {
        "document_text": document_text,
        "image_paths": image_paths,
        "topic": topic,
    }
    with httpx.Client(timeout=300.0) as client:
        response = client.post(url, json=payload)
    response.raise_for_status()
    return response.json()
