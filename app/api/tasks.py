from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.task import DocumentTask, TaskStatus
from app.schemas.task import TaskCreateResponse, TaskStatusResponse
from app.services.storage import save_input_file, get_output_path, get_report_path
from app.services.validator import validate_source_document
from app.services.gost_formatter import process_document
from app.services.reporting import save_report

router = APIRouter(prefix='/tasks', tags=['tasks'])


@router.post('', response_model=TaskCreateResponse)
def create_task(
    file: UploadFile = File(...),
    faculty: str = Form(...),
    department: str = Form(...),
    lab_title: str = Form(...),
    lab_number: str = Form(...),
    student_name: str = Form(...),
    reviewer_name: str = Form(...),
    discipline: str =  Form(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Поддерживается только формат DOCX.')

    payload = {
        'faculty': faculty,
        'department': department,
        'lab_title': lab_title,
        'lab_number': lab_number,
        'student_name': student_name,
        'reviewer_name': reviewer_name,
        'discipline': discipline,
    }

    task = DocumentTask(
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
    output_path = get_output_path(task.id)
    report_path = get_report_path(task.id)

    task.input_path = input_path

    validation = validate_source_document(input_path)
    if not validation['is_valid']:
        report = {
            'status': 'failed',
            'errors': validation['errors'],
            'warnings': validation['warnings'],
            'metrics': validation['metrics'],
            'fixes': [],
        }
        save_report(report_path, report)
        task.status = TaskStatus.FAILED
        task.report_path = report_path
        task.errors = validation['errors']
        task.warnings = validation['warnings']
        db.commit()
        return TaskCreateResponse(task_id=task.id, status=task.status.value, report=report)

    report = process_document(input_path, output_path, payload)
    report['metrics'] = validation['metrics']
    report['warnings'].extend(validation['warnings'])
    save_report(report_path, report)

    task.status = TaskStatus.COMPLETED
    task.output_path = output_path
    task.report_path = report_path
    task.errors = report['errors']
    task.warnings = report['warnings']
    db.commit()

    return TaskCreateResponse(task_id=task.id, status=task.status.value, report=report)


@router.get('/{task_id}', response_model=TaskStatusResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.get(DocumentTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена.')

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status.value,
        errors=task.errors or [],
        warnings=task.warnings or [],
        has_output=bool(task.output_path),
        has_report=bool(task.report_path),
    )


@router.get('/{task_id}/download')
def download_result(task_id: str, db: Session = Depends(get_db)):
    task = db.get(DocumentTask, task_id)
    if not task or not task.output_path:
        raise HTTPException(status_code=404, detail='Готовый файл не найден.')
    return FileResponse(task.output_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=f'{task_id}.docx')


@router.get('/{task_id}/report')
def download_report(task_id: str, db: Session = Depends(get_db)):
    task = db.get(DocumentTask, task_id)
    if not task or not task.report_path:
        raise HTTPException(status_code=404, detail='Отчёт не найден.')
    return FileResponse(task.report_path, media_type='application/json', filename=f'{task_id}.json')
