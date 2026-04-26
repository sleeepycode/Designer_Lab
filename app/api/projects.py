from pathlib import Path
import shutil

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.models.project import Project, ProjectStatus
from app.models.task import DocumentTask, TaskStatus
from app.schemas.project import (
    ProjectUploadResponse,
    ProjectStatusResponse,
    ProjectDeleteResponse,
    ProjectAnalysisResponse,
    ProjectFileUploadResponse,
)
from app.services.storage import save_project_source_file, write_project_metadata, read_project_metadata

router = APIRouter(prefix="/projects", tags=["projects"])


def _mock_analyze_project(project: Project) -> dict:
    source_ext = Path(project.source_filename).suffix.lower()
    return {
        "model": "mock-ml-v1",
        "source_extension": source_ext,
        "summary": "Анализ выполнен успешно.",
        "confidence": 0.97,
    }


def _ensure_project_owner(project: Project, user_id: str, action: str) -> None:
    if not project.user_id:
        raise HTTPException(status_code=403, detail=f"У проекта не задан владелец. {action} запрещено.")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail=f"Нельзя {action} для проекта другого пользователя.")


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
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Имя файла отсутствует.")

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
        raise HTTPException(status_code=400, detail="Поддерживаются только форматы .docx, .pdf, .png, .jpg.")

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
            "files": [{"path": source_path, "type": "input", "name": project.source_filename}],
            "analysis": None,
            "ml_suggestions": [],
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
        raise HTTPException(status_code=400, detail="Имя файла отсутствует.")

    try:
        file_path = save_project_source_file(project_id, file)
    except ValueError:
        raise HTTPException(status_code=400, detail="Поддерживаются только форматы .docx, .pdf, .png, .jpg.")

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

    project.status = ProjectStatus.ANALYZING
    db.commit()

    try:
        analysis_result = _mock_analyze_project(project)
        project.status = ProjectStatus.READY
        db.commit()
        metadata = read_project_metadata(project.id) or _build_project_metadata(project)
        metadata_block = metadata.get("metadata", {})
        metadata_block["analysis"] = analysis_result
        metadata_block["ml_suggestions"] = [
            "Проверить корректность титульного листа.",
            "Сверить формат ссылок с требованиями ГОСТ.",
        ]
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
