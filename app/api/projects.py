from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectUploadResponse, ProjectStatusResponse
from app.services.storage import save_project_source_file, write_project_metadata

router = APIRouter(prefix="/projects", tags=["projects"])


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
        status=ProjectStatus.CREATED,
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
        "project_id": project.id,
        "user_id": user_id,
        "status": ProjectStatus.UPLOADED.value,
        "source_filename": project.source_filename,
        "source_path": source_path,
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
