"""
HTTP-клиент ML (контракт: POST /analyze).

Картинки передаются как images[].path — публичный HTTP URL на backend №1 (/storage/...).
"""

from __future__ import annotations

from pathlib import Path

import httpx

from app.core.config import settings
from app.services.storage import project_file_url, project_image_entry, storage_relative_path


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


def build_ml_images_from_paths(
    image_paths: list[str | Path],
    project_id: str | None = None,
) -> list[dict]:
    result: list[dict] = []
    for index, raw_path in enumerate(image_paths, start=1):
        path = Path(raw_path)
        if project_id:
            result.append(project_image_entry(project_id, path, index))
        else:
            result.append({
                'image_id': f'user_image_{index}',
                'path': project_file_url(path),
                'local_path': storage_relative_path(path),
                'source': 'user_uploaded_image',
                'filename': path.name,
                'position': index - 1,
            })
    return result


def analyze_images(
    image_paths: list[str | Path],
    topic: str,
    document_text: str = '',
    project_id: str | None = None,
) -> dict:
    """POST /analyze — JSON по контракту ML (images[].path = HTTP URL)."""
    base = _base_url()
    if not base:
        raise RuntimeError('Не задан ml_service_base_url в .env')

    url = f'{base}/analyze'
    payload = {
        'project_id': project_id or '',
        'document_text': document_text,
        'image_paths': [],
        'image_urls': [],
        'images': build_ml_images_from_paths(image_paths, project_id=project_id),
        'topic': topic or 'лабораторная работа',
    }
    timeout = float(settings.ml_timeout)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
    if not response.is_success:
        detail = response.text[:500]
        raise RuntimeError(f'ML analyze: {response.status_code} {detail}')
    return response.json()


def _document_text_from_extract(extract_result: dict) -> str:
    lines: list[str] = []
    for item in extract_result.get('paragraphs') or []:
        if isinstance(item, dict):
            text = (item.get('text') or '').strip()
        else:
            text = str(item).strip()
        if text:
            lines.append(text)
    return '\n'.join(lines)


def _doc_service_image_url(path: str, project_id: str) -> str:
    raw = str(path).replace('\\', '/')
    if raw.startswith('http://') or raw.startswith('https://'):
        return raw
    marker = 'storage/'
    idx = raw.lower().find(marker)
    if idx != -1:
        relative = raw[idx:]
    else:
        relative = f'storage/projects/{project_id}/media/{Path(raw).name}'
    base = (settings.doc_service_base_url or '').strip().rstrip('/')
    return f'{base}/{relative}'


def _images_for_ml_pipeline(
    extract_result: dict,
    project_id: str,
    uploaded_images: list[dict] | None,
) -> list[dict]:
    """Картинки из DOCX (URL doc-service) + user uploads (уже с HTTP URL backend №1)."""
    images: list[dict] = list(uploaded_images or [])
    seen = {img.get('path') for img in images if img.get('path')}
    for index, item in enumerate(extract_result.get('images') or [], start=1):
        if isinstance(item, dict):
            raw_path = item.get('path') or item.get('id') or ''
            image_id = str(item.get('id') or f'docx_image_{index}')
            position = item.get('position', index - 1)
            source = item.get('source', 'original_docx_image')
        else:
            raw_path = str(item)
            image_id = f'docx_image_{index}'
            position = index - 1
            source = 'original_docx_image'
        if not raw_path:
            continue
        url = _doc_service_image_url(raw_path, project_id)
        if url in seen:
            continue
        seen.add(url)
        images.append({
            'image_id': image_id,
            'path': url,
            'local_path': storage_relative_path(raw_path) if 'storage/' in raw_path.replace('\\', '/').lower() else raw_path,
            'source': source,
            'filename': Path(str(raw_path).replace('\\', '/')).name,
            'position': position,
        })
    return images


def minimal_ml_fallback(topic: str, error: str | None = None) -> dict:
    """Минимальный ml_response, если ML недоступен (локальный doc-service требует поле)."""
    out: dict = {
        'success': False,
        'topic': topic,
        'status': 'fallback',
        'generated_sections': [],
        'bibliography': [],
        'images': [],
    }
    if error:
        out['errors'] = [{'code': 'ml_unavailable', 'message': error}]
    return out


def analyze_document_for_project(
    project_id: str,
    extract_result: dict,
    topic: str,
    uploaded_images: list[dict] | None = None,
) -> dict:
    """
    POST /analyze после extract: document_text + images (doc-service + user URLs).
    Ответ передаётся в doc-service apply_ml_changes как ml_response.
    """
    base = _base_url()
    if not base:
        raise RuntimeError('Не задан ml_service_base_url в .env')

    url = f'{base}/analyze'
    payload = {
        'project_id': project_id,
        'document_text': _document_text_from_extract(extract_result),
        'image_paths': [],
        'image_urls': [],
        'images': _images_for_ml_pipeline(extract_result, project_id, uploaded_images),
        'topic': topic or 'лабораторная работа',
    }
    timeout = float(settings.ml_timeout)
    with httpx.Client(timeout=timeout) as client:
        response = client.post(url, json=payload)
    if not response.is_success:
        detail = response.text[:500]
        raise RuntimeError(f'ML analyze: {response.status_code} {detail}')
    return response.json()


def analyze_image_file(
    image_path: Path,
    topic: str,
    document_text: str = '',
    project_id: str | None = None,
) -> dict:
    """Анализ одного изображения: один элемент из поля images ответа ML."""
    result = analyze_images(
        [image_path],
        topic,
        document_text,
        project_id=project_id,
    )
    images = result.get('images') or []
    if images:
        return images[0]
    errors = result.get('errors') or []
    if errors:
        raise RuntimeError(str(errors[0]))
    raise RuntimeError('ML не вернул данные по изображению')
