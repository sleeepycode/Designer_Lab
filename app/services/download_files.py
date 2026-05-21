"""Разрешение путей для скачивания PDF / DOCX."""

from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.task import DocumentTask, TaskStatus


def _media_for_format(fmt: str) -> tuple[str, str]:
    if fmt == 'pdf':
        return 'application/pdf', 'pdf'
    if fmt == 'docx':
        return (
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'docx',
        )
    raise HTTPException(
        status_code=400,
        detail='Параметр format должен быть pdf или docx.',
    )


def task_output_flags(task: DocumentTask) -> dict[str, bool]:
    paths = (task.payload or {}).get('output_paths') or {}
    pdf = paths.get('pdf') or task.output_path
    docx = paths.get('docx')
    pdf_ok = bool(pdf and Path(pdf).is_file())
    docx_ok = bool(docx and Path(docx).is_file())
    return {
        'has_output_pdf': pdf_ok,
        'has_output_docx': docx_ok,
        'has_output': pdf_ok or docx_ok,
    }


def resolve_task_output(task: DocumentTask, fmt: str) -> tuple[Path, str, str]:
    media_type, ext = _media_for_format(fmt)
    paths = (task.payload or {}).get('output_paths') or {}
    candidate = paths.get(fmt) or (task.output_path if fmt == 'pdf' and task.output_path else None)
    if not candidate:
        candidate = str(Path(settings.output_dir) / f'{task.id}.{ext}')
    path = Path(candidate)
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f'Файл {fmt.upper()} не найден.')
    return path, media_type, f'{task.id}.{ext}'


def resolve_project_output(
    db: Session,
    project_id: str,
    fmt: str,
) -> tuple[Path, str, str]:
    media_type, ext = _media_for_format(fmt)
    project_output_dir = Path(settings.projects_dir) / project_id / 'output'
    files = sorted(
        project_output_dir.glob(f'*.{ext}'),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if files:
        path = files[0]
        return path, media_type, f'{project_id}_result.{ext}'

    stmt = (
        select(DocumentTask)
        .where(DocumentTask.project_id == project_id)
        .where(DocumentTask.status == TaskStatus.COMPLETED)
        .order_by(DocumentTask.created_at.desc())
        .limit(1)
    )
    task = db.execute(stmt).scalars().first()
    if not task:
        raise HTTPException(status_code=404, detail='Готовый файл проекта не найден.')
    return resolve_task_output(task, fmt)
