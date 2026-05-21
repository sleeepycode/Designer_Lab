from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
from app.models.task import DocumentTask, TaskStatus
from app.services import orchestrator
from app.services.reporting import save_report
from app.services.storage import (
    get_output_path,
    get_report_path,
    get_project_root,
    read_project_metadata,
    save_project_output_file,
    write_project_metadata,
)
from app.core.errors import raise_api_error
from app.services.validator import validate_source_document


def _sync_project_metadata_snapshot(project: Project) -> dict[str, Any]:
    return {
        'project_id': project.id,
        'user_id': project.user_id,
        'status': project.status.value,
        'source_path': project.source_path,
        'created_at': project.created_at.isoformat() if project.created_at else None,
        'updated_at': project.updated_at.isoformat() if project.updated_at else None,
    }


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

    output_path = get_output_path(task.id)
    report_path = get_report_path(task.id)
    task.input_path = input_path
    doc_service_project_id = project.id if project else task.id

    metadata_topic: str | None = None
    if project:
        meta = read_project_metadata(project.id)
        metadata_topic = meta.get('metadata', {}).get('topic')

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
        return {'type': 'validation_failed', 'report': report}

    _update_project_status(db, project, ProjectStatus.PROCESSING)

    try:
        extracted = orchestrator.extract_via_doc_service(Path(input_path), doc_service_project_id)
        document_text = orchestrator.text_from_extracted(extracted, input_path)
        image_paths = orchestrator.collect_image_paths(project, extracted, get_project_root)
        topic = orchestrator.topic_from_context(task.payload, metadata_topic)

        _update_project_status(db, project, ProjectStatus.ANALYZING)
        try:
            ml_response = orchestrator.run_ml_analysis(document_text, image_paths, topic)
        finally:
            _update_project_status(db, project, ProjectStatus.PROCESSING)

        title_page = orchestrator.title_page_from_form(task.payload)
        orchestrator.build_doc_service_result(
            doc_service_project_id,
            ml_response,
            title_page,
            output_path,
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
                'steps': ['validate', 'doc_service.extract', 'ml.analyze', 'doc_service.apply_ml_changes', 'doc_service.download'],
            },
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
                meta = read_project_metadata(project.id)
                mb = meta.get('metadata', {})
                errs = mb.get('processing_errors', [])
                errs.append(str(exc))
                mb['processing_errors'] = errs
                meta['metadata'] = mb
                meta['db_snapshot'] = _sync_project_metadata_snapshot(project)
                write_project_metadata(project.id, meta)
            except Exception:
                pass
        raise HTTPException(status_code=400, detail=f'Ошибка обработки: {exc}')

    save_report(report_path, report)
    task.status = TaskStatus.COMPLETED
    task.output_path = output_path
    task.report_path = report_path
    task.errors = report['errors']
    task.warnings = report['warnings']
    db.commit()

    if project:
        try:
            project_output_path = save_project_output_file(project.id, task.id, output_path)
            metadata = read_project_metadata(project.id)
            metadata_block = metadata.get('metadata', {})
            files = metadata_block.get('files', [])
            files.append({'path': project_output_path, 'type': 'output', 'name': f'{task.id}.docx'})
            metadata_block['files'] = files
            metadata_block['last_task_report_path'] = report_path
            metadata_block['ml_result'] = ml_response
            metadata_block['ml_analysis'] = ml_response
            metadata['metadata'] = metadata_block
            metadata['db_snapshot'] = _sync_project_metadata_snapshot(project)
            write_project_metadata(project.id, metadata)
        except Exception:
            pass
        _update_project_status(db, project, ProjectStatus.READY)

    return {
        'type': 'success',
        'report': report,
        'output_path': output_path,
        'report_path': report_path,
    }
