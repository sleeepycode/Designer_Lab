"""HTTP-клиент doc-service (ветка doc-service)."""

from __future__ import annotations

from pathlib import Path

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
    base = (settings.doc_service_base_url or "").strip().rstrip("/")
    if not base:
        raise RuntimeError("Не задан doc_service_base_url в .env")
    return base


def extract_document(docx_path: Path, project_id: str | None = None) -> dict:
    url = f"{_base_url()}/documents/extract"
    data: dict[str, str] = {}
    if project_id:
        data["project_id"] = project_id
    with docx_path.open("rb") as f:
        files = {
            "file": (
                docx_path.name,
                f,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, files=files, data=data or None)
    response.raise_for_status()
    return response.json()


def apply_ml_changes(project_id: str, ml_response: dict, title_page: dict) -> None:
    url = f"{_base_url()}/documents/apply_ml_changes"
    body = {
        "project_id": project_id,
        "ml_response": ml_response,
        "title_page": title_page,
    }
    with httpx.Client(timeout=300.0) as client:
        response = client.post(url, json=body)
    response.raise_for_status()


def download_result(project_id: str, dest_path: str | Path) -> Path:
    url = f"{_base_url()}/documents/download/{project_id}"
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120.0) as client:
        response = client.get(url)
    response.raise_for_status()
    dest.write_bytes(response.content)
    return dest
