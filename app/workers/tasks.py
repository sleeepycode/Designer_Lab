import json
import traceback
import requests
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.celery import celery_app
from app.core.db import SessionLocal
from app.models.task import DocumentTask, TaskStatus
from app.core.config import settings
from app.services.validator import validate_source_document
from app.services.gost_applier import process_document
from app.services.reporting import save_report
from app.services.title_page_generator import generate_title_page


@celery_app.task(bind=True, name='document_service.process_document')
def process_document_task(
    self,
    task_id: str,
    input_path: str,
    user_id: str,
    title_page_data: dict,
):
    """Основная задача обработки документа"""
    db: Session = SessionLocal()
    task = None
    
    try:
        # Получить задачу из БД
        task = db.query(DocumentTask).filter(DocumentTask.id == task_id).first()
        if not task:
            raise Exception(f'Task {task_id} not found in database')
        
        # Обновить статус
        task.status = TaskStatus.PROCESSING
        db.commit()
        
        # Валидация входного файла
        validation_result = validate_source_document(input_path)
        if not validation_result.get('is_valid', False):
            task.errors = validation_result.get('errors', [])
            task.warnings = validation_result.get('warnings', [])
            task.status = TaskStatus.FAILED
            db.commit()
            _send_callback(task)
            return {
                'status': 'failed',
                'task_id': task_id,
                'errors': validation_result.get('errors', [])
            }
        
        # Обработка документа по ГОСТ
        formatted_path = Path(settings.output_dir) / f'{task_id}_formatted.docx'
        result = process_document(
            input_path=input_path,
            output_path=str(formatted_path),
            payload=title_page_data,
        )

        if result['status'] != 'completed':
            task.status = TaskStatus.FAILED
            task.errors = result.get('errors', [])
            task.warnings = result.get('warnings', [])
            db.commit()
            _send_callback(task)
            return {
                'status': 'failed',
                'task_id': task_id,
                'errors': result.get('errors', [])
            }

        # Генерация титульной страницы
        output_path = Path(settings.output_dir) / f'{task_id}_output.docx'
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

        # Сохранение отчета
        report_path = Path(settings.report_dir) / f'{task_id}_report.json'
        report_data = {
            'task_id': task_id,
            'user_id': user_id,
            'filename': task.original_filename,
            'status': 'completed',
            'warnings': result.get('warnings', []),
            'processing_info': result.get('processing_info', {}),
        }
        save_report(str(report_path), report_data)
        
        # Обновить задачу в БД
        task.status = TaskStatus.COMPLETED
        task.output_path = str(output_path)
        task.report_path = str(report_path)
        task.warnings = result.get('warnings', [])
        task.result = report_data
        db.commit()
        
        # Отправить callback
        _send_callback(task)
        
        return {
            'status': 'completed',
            'task_id': task_id,
            'output_path': str(output_path),
            'report_path': str(report_path),
        }
        
    except Exception as e:
        error_msg = f'{str(e)}\n{traceback.format_exc()}'
        
        if task:
            task.status = TaskStatus.FAILED
            task.errors = [error_msg]
            db.commit()
            _send_callback(task)
        
        return {
            'status': 'failed',
            'task_id': task_id,
            'error': error_msg,
        }
    
    finally:
        db.close()


def _send_callback(task: DocumentTask):
    """Отправить callback на main backend"""
    if not task.callback_url:
        return
    
    try:
        payload = {
            'task_id': task.id,
            'user_id': task.user_id,
            'status': task.status.value,
            'errors': task.errors or [],
            'warnings': task.warnings or [],
            'output_url': f'{settings.main_backend_url}/api/documents/output/{task.id}' if task.output_path else None,
            'report_url': f'{settings.main_backend_url}/api/documents/report/{task.id}' if task.report_path else None,
            'result': task.result,
        }
        
        response = requests.post(
            task.callback_url,
            json=payload,
            timeout=10,
            headers={'X-API-Key': settings.api_key}
        )
        response.raise_for_status()
        
    except Exception as e:
        print(f'Failed to send callback for task {task.id}: {str(e)}')
