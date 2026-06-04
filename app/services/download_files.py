"""Разрешение путей для скачивания готового DOCX."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.task import DocumentTask, TaskStatus

DOCX_MEDIA = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'


def _normalize_format(fmt: str) -> str:
    normalized = fmt.lower().strip()
    if normalized == 'pdf':
        raise HTTPException(
            status_code=400,
            detail='Скачивание PDF отключено. Используйте format=docx.',
        )
    if normalized != 'docx':
        raise HTTPException(
            status_code=400,
            detail='Доступен только format=docx.',
        )
    return normalized


def task_output_flags(task: DocumentTask) -> dict[str, bool]:
    paths = (task.payload or {}).get('output_paths') or {}
    docx = paths.get('docx') or task.output_path
    docx_ok = bool(docx and Path(docx).is_file())
    return {
        'has_output_pdf': False,
        'has_output_docx': docx_ok,
        'has_output': docx_ok,
    }


def resolve_task_output(task: DocumentTask, fmt: str) -> tuple[Path, str, str]:
    _normalize_format(fmt)
    paths = (task.payload or {}).get('output_paths') or {}
    candidate = paths.get('docx') or task.output_path
    if not candidate:
        candidate = str(Path(settings.output_dir) / f'{task.id}.docx')
    path = Path(candidate)
    if not path.is_file():
        raise HTTPException(status_code=404, detail='Готовый DOCX не найден.')
    return path, DOCX_MEDIA, f'{task.id}.docx'


def resolve_project_output(
    db: Session,
    project_id: str,
    fmt: str,
) -> tuple[Path, str, str]:
    _normalize_format(fmt)
    project_output_dir = Path(settings.projects_dir) / project_id / 'output'
    files = sorted(
        project_output_dir.glob('*.docx'),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if files:
        path = files[0]
        return path, DOCX_MEDIA, f'{project_id}_result.docx'

    stmt = (
        select(DocumentTask)
        .where(DocumentTask.project_id == project_id)
        .where(DocumentTask.status == TaskStatus.COMPLETED)
        .order_by(DocumentTask.created_at.desc())
        .limit(1)
    )
    task = db.execute(stmt).scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail='Готовый DOCX проекта не найден.')
    return resolve_task_output(task, 'docx')
