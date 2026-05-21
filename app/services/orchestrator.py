"""
Связка Frontend → Backend №1 → doc-service → ML → doc-service → Backend №1 → Frontend.

Фронт ходит только сюда. ML и doc-service — по HTTP, фронт их не вызывает.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docx import Document

from app.models.project import Project
from app.services import doc_service_client, ml_client


def check_integrations() -> dict[str, Any]:
    """Проверка доступности doc-service и ML (для /health и отладки)."""
    return {
        'doc_service': doc_service_client.ping(),
        'ml': ml_client.ping(),
    }


def extract_via_doc_service(docx_path: Path, project_id: str) -> dict:
    return doc_service_client.extract_document(docx_path, project_id)


def normalize_extract_for_frontend(raw: dict) -> dict:
    """
    Ответ doc-service → формат фронта (API_CONTRACT): paragraphs — строки.
    """
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

    return {
        'paragraphs': paragraphs,
        'tables': tables,
        'images': images,
    }


def text_from_extracted(extracted: dict, fallback_docx_path: str | None = None) -> str:
    paragraphs = extracted.get('paragraphs') or []
    parts: list[str] = []
    for item in paragraphs:
        if isinstance(item, dict):
            text = (item.get('text') or '').strip()
        else:
            text = str(item).strip()
        if text:
            parts.append(text)
    document_text = '\n'.join(parts)
    if document_text.strip() or not fallback_docx_path:
        return document_text
    return '\n'.join(
        p.text.strip()
        for p in Document(fallback_docx_path).paragraphs
        if p.text and p.text.strip()
    )


def collect_image_paths(project: Project | None, extracted: dict, project_root_fn) -> list[str]:
    paths: list[str] = []
    for img in extracted.get('images') or []:
        if isinstance(img, dict) and img.get('path'):
            paths.append(str(img['path']))
        elif isinstance(img, str):
            paths.append(img)

    if project:
        images_dir = project_root_fn(project.id) / 'images'
        if images_dir.is_dir():
            for ext in ('*.png', '*.jpg', '*.jpeg'):
                for p in sorted(images_dir.glob(ext)):
                    resolved = str(p.resolve())
                    if resolved not in paths:
                        paths.append(resolved)
    return paths


def run_ml_analysis(document_text: str, image_paths: list[str], topic: str) -> dict:
    return ml_client.analyze_document(document_text, image_paths, topic)


def build_doc_service_result(
    project_id: str,
    ml_response: dict,
    title_page: dict,
    output_path: str | Path,
) -> Path:
    doc_service_client.apply_ml_changes(project_id, ml_response, title_page)
    return doc_service_client.download_result(project_id, output_path)


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
