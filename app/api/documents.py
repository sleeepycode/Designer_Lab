from pathlib import Path

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.db import get_db
from app.core.config import settings
from app.models.task import DocumentTask, TaskStatus
from app.schemas.task import (
    ProcessDocumentRequest,
    ProcessDocumentResponse,
    TaskStatusResponse,
    TaskResultResponse,
)
from app.services.storage import save_input_file, get_output_path, get_report_path
from app.services.validator import validate_source_document
from app.services.gost_applier import process_document as apply_gost_document
from app.services.title_page_generator import generate_title_page
from app.services.reporting import save_report

router = APIRouter(prefix='/api/documents', tags=['documents'])


def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Проверка API ключа"""
    if x_api_key is None:
        raise HTTPException(status_code=401, detail='API Key не предоставлен')
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail='Неверный API Key')
    return x_api_key


@router.post('/process', response_model=ProcessDocumentResponse)
async def process_document(
    file: UploadFile = File(..., description="DOCX файл для обработки"),
    title_page: str = Form(
        ...,
        description="""JSON строка с данными титульной страницы. Пример:
        {"faculty": "ФКН", "department": "ИПП", "lab_title": "Работа", "lab_number": "1", 
         "student_group": "БПМ191", "student_name": "Иван Иванов", "reviewer_name": "Петр Петров", 
         "discipline": "Python"}"""
    ),
    _: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Загрузить документ на обработку"""
    import json
    
    try:
        title_page_data = json.loads(title_page)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Некорректный JSON для title_page')
    
    # Создать задачу в БД (БЕЗ сохранения файла)
    task = DocumentTask(
        original_filename=file.filename or 'document.docx',
        input_path='',  # будет установлено после
        payload=title_page_data,
        status=TaskStatus.PROCESSING,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    input_path = save_input_file(task.id, file)
    task.input_path = input_path
    db.commit()

    validation_result = validate_source_document(input_path)
    if not validation_result.get('is_valid', False):
        task.status = TaskStatus.FAILED
        task.errors = validation_result.get('errors', [])
        task.warnings = validation_result.get('warnings', [])
        db.commit()
        return ProcessDocumentResponse(
            task_id=task.id,
            status=task.status.value,
            message='Валидация завершилась с ошибками',
        )

    formatted_path = Path(settings.output_dir) / f'{task.id}_formatted.docx'
    result = apply_gost_document(
        input_path=input_path,
        output_path=str(formatted_path),
        payload=title_page_data,
    )

    if result['status'] != 'completed':
        task.status = TaskStatus.FAILED
        task.errors = result.get('errors', [])
        task.warnings = result.get('warnings', [])
        db.commit()
        return ProcessDocumentResponse(
            task_id=task.id,
            status=task.status.value,
            message='Ошибка обработки документа',
        )

    output_path = Path(settings.output_dir) / f'{task.id}_output.docx'
    generate_title_page(
        input_path=str(formatted_path),
        output_path=str(output_path),
        department=title_page_data.get('department', ''),
        discipline=title_page_data.get('discipline', ''),
        lab_number=title_page_data.get('lab_number', ''),
        topic=title_page_data.get('lab_title', ''),
        full_name=title_page_data.get('student_name', ''),
        group=title_page_data.get('student_group', ''),
        teacher=title_page_data.get('reviewer_name', ''),
    )

    report_path = Path(settings.report_dir) / f'{task.id}_report.json'
    report_data = {
        'task_id': task.id,
        'status': 'completed',
        'filename': task.original_filename,
        'warnings': result.get('warnings', []),
        'processing_info': result.get('processing_info', {}),
    }
    save_report(str(report_path), report_data)

    task.status = TaskStatus.COMPLETED
    task.output_path = str(output_path)
    task.report_path = str(report_path)
    task.warnings = result.get('warnings', [])
    task.result = report_data
    db.commit()

    return ProcessDocumentResponse(
        task_id=task.id,
        status=task.status.value,
        message='Документ обработан успешно',
    )


@router.get('/status/{task_id}', response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    _: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Получить статус задачи"""
    task = db.execute(select(DocumentTask).where(DocumentTask.id == task_id)).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена')
    
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status.value,
        original_filename=task.original_filename,
        created_at=task.created_at,
        updated_at=task.updated_at,
        errors=task.errors or [],
        warnings=task.warnings or [],
        has_output=task.output_path is not None,
        has_report=task.report_path is not None,
    )


@router.get('/result/{task_id}', response_model=TaskResultResponse)
async def get_task_result(
    task_id: str,
    _: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Получить результат обработки"""
    task = db.execute(select(DocumentTask).where(DocumentTask.id == task_id)).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена')
    
    return TaskResultResponse(
        task_id=task.id,
        status=task.status.value,
        errors=task.errors or [],
        warnings=task.warnings or [],
        result=task.result,
    )


@router.get('/output/{task_id}')
async def download_output(
    task_id: str,
    _: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Скачать обработанный документ"""
    task = db.execute(select(DocumentTask).where(DocumentTask.id == task_id)).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена')
    
    if not task.output_path or not Path(task.output_path).exists():
        raise HTTPException(status_code=404, detail='Выходной файл не найден')
    
    return FileResponse(
        path=task.output_path,
        filename=f'processed_{task.original_filename}',
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


@router.get('/report/{task_id}')
async def download_report(
    task_id: str,
    _: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Скачать отчет об обработке"""
    task = db.execute(select(DocumentTask).where(DocumentTask.id == task_id)).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена')
    
    if not task.report_path or not Path(task.report_path).exists():
        raise HTTPException(status_code=404, detail='Отчет не найден')
    
    return FileResponse(
        path=task.report_path,
        filename=f'report_{task.original_filename}.json',
        media_type='application/json'
    )


@router.delete('/{task_id}')
async def delete_task(
    task_id: str,
    _: str = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Удалить задачу и её файлы"""
    task = db.execute(select(DocumentTask).where(DocumentTask.id == task_id)).scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail='Задача не найдена')
    
    # Удалить файлы
    for path in [task.input_path, task.output_path, task.report_path]:
        if path and Path(path).exists():
            Path(path).unlink()
    
    # Удалить из БД
    db.delete(task)
    db.commit()
    
    return {'status': 'deleted', 'task_id': task_id}


@router.get('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'ok', 'service': 'document-processing-service'}
