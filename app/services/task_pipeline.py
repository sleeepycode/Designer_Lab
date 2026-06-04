from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.task import DocumentTask, TaskStatus
from app.services import orchestrator
from app.services import project_metadata as pm
from app.services.reporting import save_report
from app.services.storage import (
    get_task_output_paths,
    get_report_path,
    list_project_uploaded_images,
    save_project_output_files,
)
from app.core.errors import raise_api_error
from app.services.validator import validate_source_document


def _update_project_status(db: Session, project: Project | None, status: ProjectStatus) -> None:
    if project is None:
        return
    project.status = status
    db.commit()


def run_document_task_pipeline(
    db: Session,
    task: DocumentTask,
    project: Project | None,
    input_path: str,
) -> dict[str, Any]:
    if Path(input_path).stat().st_size == 0:
        task.status = TaskStatus.FAILED
        task.errors = ['Входной файл пустой.']
        db.commit()
        _update_project_status(db, project, ProjectStatus.ERROR)
        raise_api_error('empty_file', 'Входной файл пустой.')

    output_docx = get_task_output_paths(task.id)['docx']
    report_path = get_report_path(task.id)
    task.input_path = input_path
    doc_service_project_id = project.id if project else task.id

    metadata_topic: str | None = None
    if project:
        metadata_topic = pm.topic_value(pm.load(project))

    try:
        validation = validate_source_document(input_path)
    except Exception:
        task.status = TaskStatus.FAILED
        task.errors = ['Не удалось прочитать DOCX. Проверьте, что файл не поврежден.']
        db.commit()
        _update_project_status(db, project, ProjectStatus.ERROR)
        raise_api_error(
            'corrupted_docx',
            'Не удалось прочитать DOCX. Проверьте, что файл не поврежден.',
        )

    if not validation['is_valid']:
        report = {
            'status': 'failed',
            'code': 'document_content_invalid',
            'message': validation['errors'][0] if validation['errors'] else 'Документ не прошёл проверку.',
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
        _update_project_status(db, project, ProjectStatus.ERROR)
        if project:
            meta = pm.load(project)
            for err in validation['errors']:
                pm.add_error(meta, err)
            pm.save(project, meta)
        return {'type': 'validation_failed', 'report': report}

    _update_project_status(db, project, ProjectStatus.PROCESSING)

    try:
        topic = orchestrator.topic_from_context(task.payload, metadata_topic)
        title_page = orchestrator.title_page_from_form(task.payload)

        uploaded_images: list[dict] = []
        if project:
            uploaded_images = list_project_uploaded_images(project.id)

        _update_project_status(db, project, ProjectStatus.ANALYZING)
        try:
            process_result = orchestrator.run_doc_service_pipeline(
                Path(input_path),
                doc_service_project_id,
                title_page,
                topic,
                output_docx,
                uploaded_images=uploaded_images,
            )
        finally:
            _update_project_status(db, project, ProjectStatus.PROCESSING)

        apply_result = process_result.get('apply_result') or process_result
        ml_response = process_result.get('ml_response') or (
            apply_result.get('ml_response') if isinstance(apply_result, dict) else apply_result
        )
        report = {
            'status': 'completed',
            'errors': [],
            'warnings': validation['warnings'],
            'metrics': validation['metrics'],
            'fixes': [],
            'pipeline': {
                'doc_service_project_id': doc_service_project_id,
                'topic': topic,
                'uploaded_images_count': len(uploaded_images),
                'uploaded_images': uploaded_images,
                'steps': [
                    'validate',
                    'doc_service.extract',
                    'ml.analyze',
                    'doc_service.apply_ml_changes',
                    'doc_service.download_docx',
                ],
            },
            'outputs': {'docx': output_docx},
            'ml_response': ml_response,
            'extract': process_result.get('extract'),
            'apply_result': apply_result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.errors = [str(exc)]
        db.commit()
        _update_project_status(db, project, ProjectStatus.ERROR)
        if project:
            try:
                meta = pm.load(project)
                pm.add_error(meta, str(exc))
                pm.save(project, meta)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=f'Ошибка обработки: {exc}')

    save_report(report_path, report)
    task.status = TaskStatus.COMPLETED
    task.output_path = output_docx
    task.payload = {
        **(task.payload or {}),
        'output_paths': {'docx': output_docx},
    }
    task.report_path = report_path
    task.errors = report['errors']
    task.warnings = report['warnings']
    db.commit()

    if project:
        try:
            project_outputs = save_project_output_files(project.id, task.id, output_docx)
            meta = pm.load(project)
            pm.set_outputs(meta, docx_path=project_outputs['docx'])
            meta['ml_result'] = ml_response
            meta['uploaded_images'] = uploaded_images
            meta['last_task_report_path'] = report_path
            meta['errors'] = []
            pm.save(project, meta)
        except Exception:
            pass
        _update_project_status(db, project, ProjectStatus.READY)

    return {
        'type': 'success',
        'report': report,
        'output_path': output_docx,
        'output_docx_path': output_docx,
        'report_path': report_path,
    }
