from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.core.config import settings
from app.core.errors import require_docx_upload, raise_api_error
from app.models.task import DocumentTask, TaskStatus
from app.models.project import Project, ProjectStatus
from app.schemas.task import (
    TaskCreateResponse,
    TaskStatusResponse,
    TaskHistoryItem,
    TaskHistoryResponse,
    TaskDeleteResponse,
)
from app.services.download_files import resolve_task_output, task_output_flags
from app.services.storage import save_input_file, get_report_path
from app.services.task_pipeline import run_document_task_pipeline
from app.services import orchestrator

router = APIRouter(prefix='/tasks', tags=['tasks'])


def _get_project_or_404(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Проект не найден.')
    return project


def _update_project_status(db: Session, project: Project | None, status: ProjectStatus) -> None:
    if project is None:
        return
    project.status = status
    db.commit()


@router.post('', response_model=TaskCreateResponse)
def create_task(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    project_id: str | None = Form(default=None),
    faculty: str = Form(...),
    department: str = Form(...),
    student_group: str = Form(...),
    lab_title: str = Form(...),
    lab_number: str = Form(...),
    student_name: str = Form(...),
    reviewer_name: str = Form(...),
    discipline: str =  Form(...),
    db: Session = Depends(get_db),
):
    require_docx_upload(file.filename)

    project: Project | None = None
    if project_id:
        project = _get_project_or_404(db, project_id)
        if not user_id:
            raise HTTPException(status_code=400, detail='Для привязки задачи к проекту требуется user_id.')
        if project.user_id and project.user_id != user_id:
            raise HTTPException(status_code=403, detail='Проект принадлежит другому пользователю.')

    payload = {
        'faculty': faculty,
        'department': department,
        'student_group': student_group,
        'lab_title': lab_title,
        'lab_number': lab_number,
        'student_name': student_name,
        'reviewer_name': reviewer_name,
        'discipline': discipline,
    }

    task = DocumentTask(
        user_id=user_id,
        project_id=project_id,
        original_filename=file.filename,
        input_path='',
        payload=payload,
        status=TaskStatus.CREATED,
        errors=[],
        warnings=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    input_path = save_input_file(task.id, file)
    _update_project_status(db, project, ProjectStatus.PROCESSING)

    result = run_document_task_pipeline(db, task, project, input_path)
    if result["type"] == "validation_failed":
        return TaskCreateResponse(task_id=task.id, status=task.status.value, report=result["report"])
    return TaskCreateResponse(task_id=task.id, status=task.status.value, report=result["report"])


@router.get('', response_model=TaskHistoryResponse)
def list_tasks(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(DocumentTask)
    if user_id:
        stmt = stmt.where(DocumentTask.user_id == user_id)
    stmt = stmt.order_by(DocumentTask.created_at.desc()).limit(limit)
    tasks = db.execute(stmt).scalars().all()
    items = [
        TaskHistoryItem(
            task_id=task.id,
            user_id=task.user_id,
            project_id=task.project_id,
            status=task.status.value,
            original_filename=task.original_filename,
            created_at=task.created_at,
            has_output=bool(task.output_path),
            has_report=bool(task.report_path),
        )
        for task in tasks
    ]
    return TaskHistoryResponse(items=items)


@router.get('/{task_id}', response_model=TaskStatusResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(DocumentTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена.')

    flags = task_output_flags(task)
    return TaskStatusResponse(
        task_id=task.id,
        user_id=task.user_id,
        project_id=task.project_id,
        status=task.status.value,
        errors=task.errors or [],
        warnings=task.warnings or [],
        has_output=flags['has_output'],
        has_output_pdf=flags['has_output_pdf'],
        has_output_docx=flags['has_output_docx'],
        has_report=bool(task.report_path),
    )


@router.get('/{task_id}/download')
def download_result(
    task_id: str,
    user_id: str = Query(..., description='Идентификатор пользователя'),
    format: str = Query(
        default='pdf',
        alias='format',
        description='Формат: pdf или docx',
    ),
    db: Session = Depends(get_db),
):
    task = db.get(DocumentTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена.')
    if not task.user_id:
        raise HTTPException(status_code=403, detail='У задачи не задан владелец. Скачивание запрещено.')
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail='Нельзя скачать файл другой пользователя.')
    fmt = format.lower().strip()
    path, media_type, filename = resolve_task_output(task, fmt)
    return FileResponse(str(path), media_type=media_type, filename=filename)


@router.get('/{task_id}/report')
def download_report(
    task_id: str,
    user_id: str = Query(..., description='Идентификатор пользователя'),
    db: Session = Depends(get_db),
):
    task = db.get(DocumentTask, task_id)
    if not task or not task.report_path:
        raise HTTPException(status_code=404, detail='Отчёт не найден.')
    if not task.user_id:
        raise HTTPException(status_code=403, detail='У задачи не задан владелец. Скачивание отчёта запрещено.')
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail='Нельзя скачать отчёт другой пользователя.')
    return FileResponse(task.report_path, media_type='application/json', filename=f'{task_id}.json')


@router.delete('/{task_id}', response_model=TaskDeleteResponse)
def delete_task(
    task_id: str,
    user_id: str = Query(..., description='Идентификатор пользователя'),
    db: Session = Depends(get_db),
):
    task = db.get(DocumentTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена.')
    if not task.user_id:
        raise HTTPException(status_code=403, detail='У задачи не задан владелец. Удаление запрещено.')
    if task.user_id != user_id:
        raise HTTPException(status_code=403, detail='Нельзя удалить задачу другого пользователя.')

    paths_to_delete = [task.input_path, task.report_path, task.output_path]
    output_paths = (task.payload or {}).get('output_paths') or {}
    paths_to_delete.extend(output_paths.values())
    for file_path in paths_to_delete:
        if file_path:
            path = Path(file_path)
            if path.is_file():
                path.unlink()

    db.delete(task)
    db.commit()
    return TaskDeleteResponse(task_id=task_id, status='deleted')


@router.post('/extract', response_model=dict)
def extract_docx(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    require_docx_upload(file.filename)

    task = DocumentTask(
        user_id=user_id,
        original_filename=file.filename,
        input_path='',
        payload={},
        status=TaskStatus.CREATED,
        errors=[],
        warnings=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    input_path = save_input_file(task.id, file)
    if Path(input_path).stat().st_size == 0:
        task.status = TaskStatus.FAILED
        task.errors = ['Входной файл пустой.']
        db.commit()
        raise HTTPException(status_code=400, detail='Входной файл пустой.')

    try:
        raw = orchestrator.extract_via_doc_service(Path(input_path), task.id)
        content = orchestrator.normalize_extract_for_frontend(raw)
        task.status = TaskStatus.COMPLETED
        db.commit()
        return content
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.errors = [str(e)]
        db.commit()
        raise HTTPException(status_code=400, detail=f'Ошибка извлечения: {str(e)}')
