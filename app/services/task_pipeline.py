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

    output_paths = get_task_output_paths(task.id)
    output_pdf = output_paths['pdf']
    output_docx = output_paths['docx']
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

        _update_project_status(db, project, ProjectStatus.ANALYZING)
        try:
            process_result = orchestrator.run_doc_service_pipeline(
                Path(input_path),
                doc_service_project_id,
                title_page,
                topic,
                output_pdf,
                output_docx,
            )
        finally:
            _update_project_status(db, project, ProjectStatus.PROCESSING)

        ml_response = process_result.get('ml_response') or process_result

        report = {
            'status': 'completed',
            'errors': [],
            'warnings': validation['warnings'],
            'metrics': validation['metrics'],
            'fixes': [],
            'pipeline': {
                'doc_service_project_id': doc_service_project_id,
                'topic': topic,
                'steps': [
                    'validate',
                    'doc_service.extract',
                    'doc_service.apply_ml_changes',
                    'doc_service.download_pdf',
                    'doc_service.download_docx',
                ],
            },
            'outputs': {'pdf': output_pdf, 'docx': output_docx},
            'ml_response': ml_response,
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
    task.output_path = output_pdf
    task.payload = {
        **(task.payload or {}),
        'output_paths': {'pdf': output_pdf, 'docx': output_docx},
    }
    task.report_path = report_path
    task.errors = report['errors']
    task.warnings = report['warnings']
    db.commit()

    if project:
        try:
            project_outputs = save_project_output_files(
                project.id, task.id, output_pdf, output_docx
            )
            meta = pm.load(project)
            pm.set_outputs(meta, docx_path=project_outputs['docx'], pdf_path=project_outputs['pdf'])
            meta['ml_result'] = ml_response
            meta['last_task_report_path'] = report_path
            meta['errors'] = []
            pm.save(project, meta)
        except Exception:
            pass
        _update_project_status(db, project, ProjectStatus.READY)

    return {
        'type': 'success',
        'report': report,
        'output_path': output_pdf,
        'output_docx_path': output_docx,
        'report_path': report_path,
    }
