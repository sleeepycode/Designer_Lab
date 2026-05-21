"""
Frontend → Backend №1 → doc-service → (ML внутри №2) → doc-service → Backend №1 → Frontend.

Сохраняем оба формата: PDF и DOCX (две кнопки на фронте).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services import doc_service_client, ml_client


def check_integrations() -> dict[str, Any]:
    out: dict[str, Any] = {'doc_service': doc_service_client.ping()}
    if ml_client.is_configured():
        out['ml'] = ml_client.ping()
    return out


def extract_via_doc_service(docx_path: Path, project_id: str) -> dict:
    return doc_service_client.extract_document(docx_path, project_id)


def normalize_extract_for_frontend(raw: dict) -> dict:
    paragraphs: list[str] = []
    for item in raw.get('paragraphs') or []:
        if isinstance(item, dict):
            text = (item.get('text') or '').strip()
        else:
            text = str(item).strip()
        if text:
            paragraphs.append(text)

    tables = raw.get('tables') or []
    images: list[str] = []
    for item in raw.get('images') or []:
        if isinstance(item, dict):
            path = item.get('path') or item.get('id')
            if path:
                images.append(str(path))
        elif isinstance(item, str) and item:
            images.append(item)

    return {'paragraphs': paragraphs, 'tables': tables, 'images': images}


def run_doc_service_pipeline(
    docx_path: Path,
    project_id: str,
    title_page: dict,
    topic: str,
    output_pdf_path: str | Path,
    output_docx_path: str | Path,
) -> dict[str, Any]:
    """
    1) POST /documents/extract
    2) POST /documents/apply_ml_changes
    3) GET /documents/download-pdf + GET /documents/download (DOCX)
    """
    doc_service_client.extract_document(docx_path, project_id)
    apply_result = doc_service_client.apply_ml_changes(project_id, title_page, topic)
    doc_service_client.download_pdf(project_id, output_pdf_path)
    doc_service_client.download_docx(project_id, output_docx_path)
    return apply_result


def title_page_from_form(payload: dict | None) -> dict:
    payload = payload or {}
    return {
        'department': payload.get('department', ''),
        'lab_title': payload.get('lab_title', ''),
        'lab_number': payload.get('lab_number', ''),
        'student_group': payload.get('student_group', ''),
        'student_name': payload.get('student_name', ''),
        'reviewer_name': payload.get('reviewer_name', ''),
        'discipline': payload.get('discipline', ''),
    }


def topic_from_context(payload: dict | None, metadata_topic: str | None = None) -> str:
    payload = payload or {}
    return (
        (metadata_topic or '').strip()
        or (payload.get('discipline') or '').strip()
        or (payload.get('lab_title') or '').strip()
        or 'лабораторная работа'
    )
