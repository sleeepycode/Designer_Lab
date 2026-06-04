"""
HTTP-клиент doc-service (бэкенд №2).
Контракт: https://sleeepycode-designer-lab-1dc4.twc1.net/docs

Backend №1 при process передаёт topic, title_page, uploaded_images (HTTP URL).
ML по user-картинкам при upload — отдельно POST /analyze (см. ml_client).
Локальный doc-service ждёт готовый `ml_response` от Backend №1 (см. `orchestrator.py`).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings


def ping() -> dict:
    base = (settings.doc_service_base_url or '').strip().rstrip('/')
    if not base:
        return {'ok': False, 'error': 'doc_service_base_url не задан'}
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f'{base}/documents/health')
        return {'ok': response.is_success, 'status_code': response.status_code}
    except Exception as exc:
        return {'ok': False, 'error': str(exc)}


def _base_url() -> str:
    base = (settings.doc_service_base_url or '').strip().rstrip('/')
    if not base:
        raise RuntimeError('Не задан doc_service_base_url в .env')
    return base


def extract_document(docx_path: Path, project_id: str | None = None) -> dict:
    """POST /documents/extract — multipart: file, project_id."""
    url = f'{_base_url()}/documents/extract'
    data: dict[str, str] = {}
    if project_id:
        data['project_id'] = project_id
    with docx_path.open('rb') as f:
        files = {
            'file': (
                docx_path.name,
                f,
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            )
        }
        timeout = float(settings.doc_service_timeout)
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, files=files, data=data or None)
    response.raise_for_status()
    return response.json()


def apply_ml_changes(
    project_id: str,
    title_page: dict,
    topic: str,
    ml_response: dict | None = None,
    uploaded_images: list[dict] | None = None,
) -> dict[str, Any]:
    """
    POST /documents/apply_ml_changes

    Бэкенд №2: extract уже выполнен для project_id → ML (по topic) → сборка DOCX.
    uploaded_images — картинки пользователя с HTTP path (см. list_project_uploaded_images).
    """
    url = f'{_base_url()}/documents/apply_ml_changes'
    body: dict[str, Any] = {
        'project_id': project_id,
        'title_page': title_page,
        'topic': topic,
        'uploaded_images': uploaded_images or [],
    }
    if ml_response is not None:
        body['ml_response'] = ml_response

    timeout = float(settings.doc_service_timeout)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=body)

    if response.status_code >= 400:
        detail = response.text[:500]
        raise RuntimeError(f'doc-service apply_ml_changes: {response.status_code} {detail}')

    content_type = (response.headers.get('content-type') or '').lower()
    if 'application/json' in content_type and response.content:
        return response.json()
    return {'status': 'completed', 'project_id': project_id}


def get_project_info(project_id: str) -> dict[str, Any]:
    """GET /documents/info/{project_id}"""
    url = f'{_base_url()}/documents/info/{project_id}'
    timeout = float(settings.doc_service_timeout)
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url)
    response.raise_for_status()
    return response.json()


def download_docx(project_id: str, dest_path: str | Path) -> Path:
    """GET /documents/download/{project_id} — готовый DOCX."""
    url = f'{_base_url()}/documents/download/{project_id}'
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    timeout = float(settings.doc_service_timeout)
    with httpx.Client(timeout=timeout) as client:
        response = client.get(url)
    response.raise_for_status()
    dest.write_bytes(response.content)
    return dest

