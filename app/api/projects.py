from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.core.errors import require_docx_upload, require_image_upload, raise_api_error
from app.models.project import Project, ProjectStatus
from app.models.task import DocumentTask, TaskStatus
from app.schemas.project import (
    ProjectUploadResponse,
    ProjectStatusResponse,
    ProjectDeleteResponse,
    ProjectAnalysisResponse,
    ProjectFileUploadResponse,
    ProjectProcessResponse,
    ProjectSuggestionsResponse,
    ApplySuggestionsBody,
    ApplySuggestionsResponse,
)
from app.services import orchestrator
from app.services.ml_image_suggestions import build_image_suggestions_for_project
from app.services.project_docx import resolve_primary_project_docx
from app.services.storage import (
    save_project_source_file,
    write_project_metadata,
    read_project_metadata,
    copy_project_file_to_task_input,
)
from app.services.task_pipeline import run_document_task_pipeline

router = APIRouter(prefix="/projects", tags=["projects"])


def _ensure_project_owner(project: Project, user_id: str, action: str) -> None:
    if not project.user_id:
        raise HTTPException(status_code=403, detail=f"У проекта не задан владелец. {action} запрещено.")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail=f"Нельзя {action} для проекта другого пользователя.")


def _snapshot_project_row(project: Project) -> dict:
    return {
        "project_id": project.id,
        "user_id": project.user_id,
        "status": project.status.value,
        "source_path": project.source_path,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def _build_project_metadata(project: Project, extra: dict | None = None) -> dict:
    metadata = {
        "db_snapshot": {
            "project_id": project.id,
            "user_id": project.user_id,
            "status": project.status.value,
            "source_path": project.source_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        },
        "metadata": {
            "source_filename": project.source_filename,
            "files": [],
            "analysis": None,
            "ml_suggestions": [],
            "image_suggestions": [],
            "ml_analysis": None,
            "processing_errors": [],
        },
    }
    if extra:
        metadata["metadata"].update(extra)
    return metadata


@router.post("/upload", response_model=ProjectUploadResponse)
def upload_project_file(
    file: UploadFile = File(...),
    user_id: str | None = Form(default=None),
    topic: str | None = Form(default=None, description="Тема работы для ML"),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise_api_error("invalid_file_format", "Имя файла отсутствует.")
    require_docx_upload(file.filename)

    project = Project(
        user_id=user_id,
        status=ProjectStatus.UPLOADED,
        source_filename=Path(file.filename).name,
        source_path="",
        metadata_path="",
        payload=None,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    try:
        source_path = save_project_source_file(project.id, file)
    except ValueError:
        project.status = ProjectStatus.ERROR
        db.commit()
        raise_api_error("invalid_file_format", "Некорректный формат файла. Поддерживается только DOCX.")

    metadata = {
        "db_snapshot": {
            "project_id": project.id,
            "user_id": user_id,
            "status": ProjectStatus.UPLOADED.value,
            "source_path": source_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        },
        "metadata": {
            "source_filename": project.source_filename,
            "topic": (topic or "").strip() or None,
            "files": [{"path": source_path, "type": "input", "name": project.source_filename}],
            "analysis": None,
            "ml_suggestions": [],
            "image_suggestions": [],
            "ml_analysis": None,
            "processing_errors": [],
        },
    }
    metadata_path = write_project_metadata(project.id, metadata)

    project.source_path = source_path
    project.metadata_path = metadata_path
    project.status = ProjectStatus.UPLOADED
    db.commit()

    return ProjectUploadResponse(
        project_id=project.id,
        status=project.status.value,
        source_filename=project.source_filename,
    )


@router.get("/{project_id}", response_model=ProjectStatusResponse)
def get_project_status(project_id: str, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")

    return ProjectStatusResponse(
        project_id=project.id,
        user_id=project.user_id,
        status=project.status.value,
        source_filename=project.source_filename,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/{project_id}/files", response_model=ProjectFileUploadResponse)
def upload_project_additional_file(
    project_id: str,
    file: UploadFile = File(...),
    user_id: str = Form(...),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "загружать файлы")
    if not file.filename:
        raise_api_error("invalid_file_format", "Имя файла отсутствует.")
    require_image_upload(file.filename)

    try:
        file_path = save_project_source_file(project_id, file)
    except ValueError:
        raise_api_error(
            "invalid_file_format",
            "Некорректный формат файла. Для доп. загрузки поддерживаются только PNG и JPG.",
        )

    path_obj = Path(file_path)
    file_type = "image" if path_obj.parent.name == "images" else "input"

    metadata = read_project_metadata(project.id) or _build_project_metadata(project)
    metadata_block = metadata.get("metadata", {})
    files_payload = metadata_block.get("files", [])
    files_payload.append({"path": file_path, "type": file_type, "name": path_obj.name})
    metadata_block["files"] = files_payload
    metadata["metadata"] = metadata_block
    metadata["db_snapshot"] = {
        "project_id": project.id,
        "user_id": project.user_id,
        "status": project.status.value,
        "source_path": project.source_path,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }
    write_project_metadata(project.id, metadata)

    return ProjectFileUploadResponse(
        project_id=project.id,
        status=project.status.value,
        file_path=file_path,
        file_type=file_type,
    )


def _write_image_suggestions(project: Project, suggestions: list[dict]) -> None:
    metadata = read_project_metadata(project.id) or _build_project_metadata(project)
    metadata_block = metadata.get("metadata", {})
    metadata_block["image_suggestions"] = suggestions
    metadata["metadata"] = metadata_block
    metadata["db_snapshot"] = {
        "project_id": project.id,
        "user_id": project.user_id,
        "status": project.status.value,
        "source_path": project.source_path,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }
    write_project_metadata(project.id, metadata)


@router.post("/{project_id}/process", response_model=ProjectProcessResponse)
def process_project_document(
    project_id: str,
    user_id: str = Form(...),
    faculty: str = Form(...),
    department: str = Form(...),
    student_group: str = Form(...),
    lab_title: str = Form(...),
    lab_number: str = Form(...),
    student_name: str = Form(...),
    reviewer_name: str = Form(...),
    discipline: str = Form(...),
    topic: str | None = Form(default=None, description="Тема для ML (если не задана при upload)"),
    db: Session = Depends(get_db),
):
    """
    Связка: doc-service (extract) → ML → doc-service (apply + ГОСТ) → готовый файл на скачивание.
    """
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "запускать обработку")

    docx_path = resolve_primary_project_docx(project)
    if not docx_path:
        project.status = ProjectStatus.ERROR
        db.commit()
        metadata = read_project_metadata(project.id) or _build_project_metadata(project)
        metadata_block = metadata.get("metadata", {})
        errors = metadata_block.get("processing_errors", [])
        errors.append("В проекте нет DOCX для обработки (нужен .docx в загрузке или в input/).")
        metadata_block["processing_errors"] = errors
        metadata["metadata"] = metadata_block
        metadata["db_snapshot"] = {
            "project_id": project.id,
            "user_id": project.user_id,
            "status": project.status.value,
            "source_path": project.source_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }
        write_project_metadata(project.id, metadata)
        raise HTTPException(status_code=400, detail="В проекте нет DOCX для обработки.")

    payload = {
        "faculty": faculty,
        "department": department,
        "student_group": student_group,
        "lab_title": lab_title,
        "lab_number": lab_number,
        "student_name": student_name,
        "reviewer_name": reviewer_name,
        "discipline": discipline,
    }

    task = DocumentTask(
        user_id=user_id,
        project_id=project_id,
        original_filename=docx_path.name,
        input_path="",
        payload=payload,
        status=TaskStatus.CREATED,
        errors=[],
        warnings=[],
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    project.status = ProjectStatus.PROCESSING
    db.commit()

    input_path = copy_project_file_to_task_input(task.id, docx_path)

    if topic and topic.strip():
        metadata = read_project_metadata(project.id) or _build_project_metadata(project)
        mb = metadata.get("metadata", {})
        mb["topic"] = topic.strip()
        metadata["metadata"] = mb
        write_project_metadata(project.id, metadata)

    try:
        result = run_document_task_pipeline(db, task, project, input_path)
    except HTTPException as exc:
        metadata = read_project_metadata(project.id) or _build_project_metadata(project)
        metadata_block = metadata.get("metadata", {})
        errors = metadata_block.get("processing_errors", [])
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        errors.append(detail)
        metadata_block["processing_errors"] = errors
        metadata["metadata"] = metadata_block
        metadata["db_snapshot"] = {
            "project_id": project.id,
            "user_id": project.user_id,
            "status": project.status.value,
            "source_path": project.source_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }
        write_project_metadata(project.id, metadata)
        raise

    db.refresh(task)
    db.refresh(project)

    if result["type"] == "validation_failed":
        report = result["report"]
        db.refresh(project)
        return ProjectProcessResponse(
            project_id=project.id,
            task_id=task.id,
            status=project.status.value,
            report=report,
        )

    suggestions = build_image_suggestions_for_project(project.id)
    _write_image_suggestions(project, suggestions)

    db.refresh(project)
    return ProjectProcessResponse(
        project_id=project.id,
        task_id=task.id,
        status=project.status.value,
        report=result["report"],
    )


@router.get("/{project_id}/suggestions", response_model=ProjectSuggestionsResponse)
def get_image_suggestions(
    project_id: str,
    user_id: str = Query(..., description="Идентификатор пользователя"),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "смотреть подсказки")

    metadata = read_project_metadata(project.id)
    metadata_block = metadata.get("metadata", {})
    suggestions = metadata_block.get("image_suggestions")
    if not suggestions:
        suggestions = build_image_suggestions_for_project(project.id)
        _write_image_suggestions(project, suggestions)

    return ProjectSuggestionsResponse(
        project_id=project.id,
        status=project.status.value,
        suggestions=suggestions,
    )


@router.post("/{project_id}/suggestions/apply", response_model=ApplySuggestionsResponse)
def apply_image_suggestions(
    project_id: str,
    body: ApplySuggestionsBody,
    user_id: str = Query(..., description="Идентификатор пользователя"),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "применять подсказки")

    metadata = read_project_metadata(project.id) or _build_project_metadata(project)
    metadata_block = metadata.get("metadata", {})
    suggestions = metadata_block.get("image_suggestions") or []
    applied: list[str] = []
    id_set = set(body.suggestion_ids)
    for item in suggestions:
        if item.get("id") in id_set:
            item["applied"] = True
            applied.append(item["id"])
    metadata_block["image_suggestions"] = suggestions
    metadata["metadata"] = metadata_block
    metadata["db_snapshot"] = {
        "project_id": project.id,
        "user_id": project.user_id,
        "status": project.status.value,
        "source_path": project.source_path,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }
    write_project_metadata(project.id, metadata)

    return ApplySuggestionsResponse(project_id=project.id, status=project.status.value, applied_ids=applied)


@router.get("/{project_id}/download")
def download_project_result(
    project_id: str,
    user_id: str = Query(..., description="Идентификатор пользователя"),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "скачать результат")

    project_output_dir = Path(settings.projects_dir) / project_id / "output"
    output_files = sorted(
        [p for p in project_output_dir.glob("*.docx") if p.is_file()],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if output_files:
        output_path = output_files[0]
    else:
        stmt = (
            select(DocumentTask)
            .where(DocumentTask.project_id == project_id)
            .where(DocumentTask.status == TaskStatus.COMPLETED)
            .where(DocumentTask.output_path.is_not(None))
            .order_by(DocumentTask.created_at.desc())
            .limit(1)
        )
        task = db.execute(stmt).scalars().first()
        if not task or not task.output_path:
            raise HTTPException(status_code=404, detail="Готовый файл проекта не найден.")
        output_path = Path(task.output_path)
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="Готовый файл проекта не найден.")

    filename = f"{project_id}_result.docx"
    return FileResponse(
        str(output_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
    )


@router.delete("/{project_id}", response_model=ProjectDeleteResponse)
def delete_project(
    project_id: str,
    user_id: str = Query(..., description="Идентификатор пользователя"),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "удалить проект")

    related_tasks = db.execute(select(DocumentTask).where(DocumentTask.project_id == project_id)).scalars().all()
    for task in related_tasks:
        for file_path in [task.input_path, task.output_path, task.report_path]:
            if file_path:
                path = Path(file_path)
                if path.exists():
                    path.unlink()
        db.delete(task)

    project_dir = Path(settings.projects_dir) / project_id
    if project_dir.exists():
        shutil.rmtree(project_dir)

    db.delete(project)
    db.commit()
    return ProjectDeleteResponse(project_id=project_id, status="deleted")


@router.post("/{project_id}/analyze", response_model=ProjectAnalysisResponse)
def analyze_project(
    project_id: str,
    user_id: str = Query(..., description="Идентификатор пользователя"),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "запускать анализ")

    try:
        docx_path = resolve_primary_project_docx(project)
        if not docx_path:
            raise HTTPException(status_code=400, detail="В проекте нет DOCX для анализа.")

        extracted = orchestrator.extract_via_doc_service(docx_path, project.id)
        document_text = orchestrator.text_from_extracted(extracted, str(docx_path))
        image_paths = orchestrator.collect_image_paths(project, extracted, lambda pid: Path(settings.projects_dir) / pid)

        metadata = read_project_metadata(project.id) or _build_project_metadata(project)
        topic_value = orchestrator.topic_from_context(
            None,
            metadata.get("metadata", {}).get("topic") or project.source_filename,
        )

        project.status = ProjectStatus.ANALYZING
        db.commit()
        try:
            analysis_result = orchestrator.run_ml_analysis(document_text, image_paths, topic_value)
        except Exception:
            project.status = ProjectStatus.ERROR
            db.commit()
            raise

        project.status = ProjectStatus.READY
        db.commit()
        metadata_block = metadata.get("metadata", {})
        metadata_block["analysis"] = analysis_result
        metadata_block["ml_analysis"] = analysis_result
        metadata_block["ml_suggestions"] = analysis_result.get("content_suggestions") or []
        metadata_block["processing_errors"] = []
        metadata["metadata"] = metadata_block
        metadata["db_snapshot"] = {
            "project_id": project.id,
            "user_id": project.user_id,
            "status": project.status.value,
            "source_path": project.source_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }
        write_project_metadata(project.id, metadata)
        return ProjectAnalysisResponse(project_id=project.id, status=project.status.value, analysis=analysis_result)
    except Exception as exc:
        project.status = ProjectStatus.ERROR
        db.commit()
        metadata = read_project_metadata(project.id) or _build_project_metadata(project)
        metadata_block = metadata.get("metadata", {})
        errors = metadata_block.get("processing_errors", [])
        errors.append(str(exc))
        metadata_block["processing_errors"] = errors
        metadata["metadata"] = metadata_block
        metadata["db_snapshot"] = {
            "project_id": project.id,
            "user_id": project.user_id,
            "status": project.status.value,
            "source_path": project.source_path,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }
        write_project_metadata(project.id, metadata)
        raise HTTPException(status_code=400, detail=f"Ошибка ML-анализа: {str(exc)}")


@router.get("/{project_id}/analysis", response_model=ProjectAnalysisResponse)
def get_project_analysis(
    project_id: str,
    user_id: str = Query(..., description="Идентификатор пользователя"),
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Проект не найден.")
    _ensure_project_owner(project, user_id, "смотреть анализ")

    metadata = read_project_metadata(project.id)
    metadata_block = metadata.get("metadata", {})
    analysis = metadata_block.get("analysis")
    if not analysis:
        raise HTTPException(status_code=404, detail="Результат анализа пока отсутствует.")

    return ProjectAnalysisResponse(project_id=project.id, status=project.status.value, analysis=analysis)
