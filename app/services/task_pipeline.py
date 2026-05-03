from pathlib import Path
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectStatus
from app.models.task import DocumentTask, TaskStatus
from app.services.gost_applier import process_document
from app.services.gost_module_client import call_gost_module_analyze
from app.services.reporting import save_report
from app.services.storage import (
    get_output_path,
    get_report_path,
    read_project_metadata,
    save_project_output_file,
    write_project_metadata,
)
from app.services.validator import validate_source_document


def _sync_project_metadata_snapshot(project: Project) -> dict[str, Any]:
    return {
        "project_id": project.id,
        "user_id": project.user_id,
        "status": project.status.value,
        "source_path": project.source_path,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
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
    """
    Валидация + process_document + сохранение отчёта.
    Обновляет DocumentTask и при необходимости Project.
    Возвращает dict с полем type: validation_failed | success.
    Бросает HTTPException как в старом POST /tasks (пустой файл, битый docx, ошибка обработки).
    """
    if Path(input_path).stat().st_size == 0:
        task.status = TaskStatus.FAILED
        task.errors = ["Входной файл пустой."]
        db.commit()
        _update_project_status(db, project, ProjectStatus.ERROR)
        raise HTTPException(status_code=400, detail="Входной файл пустой.")

    output_path = get_output_path(task.id)
    report_path = get_report_path(task.id)
    task.input_path = input_path

    try:
        validation = validate_source_document(input_path)
    except Exception:
        task.status = TaskStatus.FAILED
        task.errors = ["Не удалось прочитать DOCX. Проверьте, что файл не поврежден."]
        db.commit()
        _update_project_status(db, project, ProjectStatus.ERROR)
        raise HTTPException(status_code=400, detail="Не удалось прочитать DOCX. Проверьте, что файл не поврежден.")

    if not validation["is_valid"]:
        report = {
            "status": "failed",
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "metrics": validation["metrics"],
            "fixes": [],
        }
        save_report(report_path, report)
        task.status = TaskStatus.FAILED
        task.report_path = report_path
        task.errors = validation["errors"]
        task.warnings = validation["warnings"]
        db.commit()
        _update_project_status(db, project, ProjectStatus.ERROR)
        return {"type": "validation_failed", "report": report}

    # processing = основной пайплайн форматирования docx (до вызова ML)
    try:
        report = process_document(input_path, output_path, task.payload or {})
    except Exception:
        task.status = TaskStatus.FAILED
        task.errors = ["Ошибка обработки документа. Проверьте входной файл."]
        db.commit()
        _update_project_status(db, project, ProjectStatus.ERROR)
        raise HTTPException(status_code=400, detail="Ошибка обработки документа. Проверьте входной файл.")

    report["metrics"] = validation["metrics"]
    report["warnings"].extend(validation["warnings"])
    save_report(report_path, report)

    task.status = TaskStatus.COMPLETED
    task.output_path = output_path
    task.report_path = report_path
    task.errors = report["errors"]
    task.warnings = report["warnings"]
    db.commit()

    project_output_path: str | None = None
    if project:
        try:
            project_output_path = save_project_output_file(project.id, task.id, output_path)
            metadata = read_project_metadata(project.id)
            metadata_block = metadata.get("metadata", {})
            files = metadata_block.get("files", [])
            files.append({"path": project_output_path, "type": "output", "name": f"{task.id}.docx"})
            metadata_block["files"] = files
            metadata_block["last_task_report_path"] = report_path
            metadata["metadata"] = metadata_block
            metadata["db_snapshot"] = _sync_project_metadata_snapshot(project)
            write_project_metadata(project.id, metadata)
        except Exception:
            pass

        base = (settings.gost_module_base_url or "").strip()
        if base:
            _update_project_status(db, project, ProjectStatus.ANALYZING)
            try:
                if not project_output_path:
                    raise RuntimeError("Не удалось подготовить DOCX в папке проекта для ML.")
                gost_data = call_gost_module_analyze(Path(project_output_path))
                if gost_data is None:
                    raise RuntimeError("Сервис gost_module недоступен (пустой URL или файл).")
                _update_project_status(db, project, ProjectStatus.READY)
                meta = read_project_metadata(project.id)
                mb = meta.get("metadata", {})
                mb["gost_module_analysis"] = gost_data
                meta["metadata"] = mb
                meta["db_snapshot"] = _sync_project_metadata_snapshot(project)
                write_project_metadata(project.id, meta)
            except Exception as exc:
                _update_project_status(db, project, ProjectStatus.ERROR)
                meta = read_project_metadata(project.id)
                mb = meta.get("metadata", {})
                errs = mb.get("processing_errors", [])
                errs.append(f"gost_module (ML): {exc}")
                mb["processing_errors"] = errs
                meta["metadata"] = mb
                meta["db_snapshot"] = _sync_project_metadata_snapshot(project)
                write_project_metadata(project.id, meta)
        else:
            _update_project_status(db, project, ProjectStatus.READY)
            try:
                meta = read_project_metadata(project.id)
                if meta:
                    meta["db_snapshot"] = _sync_project_metadata_snapshot(project)
                    write_project_metadata(project.id, meta)
            except Exception:
                pass

    return {
        "type": "success",
        "report": report,
        "output_path": output_path,
        "report_path": report_path,
    }
