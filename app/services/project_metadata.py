"""
Плоский metadata.json по архитектуре проекта (ТЗ / final_project_architecture).

Обязательные поля:
  project_id, status, topic, input_file, images, output_file, ml_result, errors

Дополнительно для API/фронта:
  source_filename, output_pdf, image_suggestions, image_ml_results, analysis, last_task_report_path
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.models.project import Project
from app.services.storage import read_project_metadata, write_project_metadata


def empty(
    project_id: str,
    *,
    status: str = "uploaded",
    topic: str | None = None,
    source_filename: str | None = None,
) -> dict[str, Any]:
    return {
        "project_id": project_id,
        "status": status,
        "topic": topic,
        "input_file": None,
        "images": [],
        "output_file": None,
        "output_pdf": None,
        "ml_result": None,
        "errors": [],
        "source_filename": source_filename,
        "image_suggestions": [],
        "image_ml_results": {},
        "analysis": None,
        "last_task_report_path": None,
    }


def normalize(raw: dict[str, Any] | None, project: Project | None = None) -> dict[str, Any]:
    """Привести к плоскому формату; поддержать старый db_snapshot + metadata."""
    if not raw:
        pid = project.id if project else ""
        return empty(pid, status=project.status.value if project else "uploaded")

    if raw.get("project_id") and "db_snapshot" not in raw and "metadata" not in raw:
        meta = dict(raw)
    else:
        snap = raw.get("db_snapshot") or {}
        inner = raw.get("metadata") or {}
        pid = snap.get("project_id") or (project.id if project else "")
        meta = empty(
            pid,
            status=snap.get("status") or (project.status.value if project else "uploaded"),
            topic=inner.get("topic"),
            source_filename=inner.get("source_filename"),
        )
        meta["input_file"] = snap.get("source_path") or inner.get("input_file")
        meta["errors"] = list(inner.get("processing_errors") or inner.get("errors") or [])
        meta["ml_result"] = inner.get("ml_result") or inner.get("ml_analysis")
        meta["analysis"] = inner.get("analysis")
        meta["image_suggestions"] = list(inner.get("image_suggestions") or [])
        meta["image_ml_results"] = dict(inner.get("image_ml_results") or {})
        meta["last_task_report_path"] = inner.get("last_task_report_path")

        images: list[str] = list(meta.get("images") or [])
        for item in inner.get("files") or []:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or Path(str(item.get("path", ""))).name
            ftype = item.get("type")
            if ftype == "image" and name and name not in images:
                images.append(name)
            elif ftype in ("input", "source") and not meta["input_file"]:
                meta["input_file"] = item.get("path")
        meta["images"] = images

        for item in inner.get("files") or []:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "output_docx":
                meta["output_file"] = item.get("path")
            elif item.get("type") == "output_pdf":
                meta["output_pdf"] = item.get("path")

        if inner.get("output_file"):
            meta["output_file"] = inner["output_file"]

    if project:
        sync_status(meta, project)
    return meta


def load(project: Project) -> dict[str, Any]:
    return normalize(read_project_metadata(project.id), project)


def save(project: Project, meta: dict[str, Any]) -> str:
    sync_status(meta, project)
    path = write_project_metadata(project.id, meta)
    project.metadata_path = path
    return path


def sync_status(meta: dict[str, Any], project: Project) -> None:
    meta["project_id"] = project.id
    meta["status"] = project.status.value
    if project.source_filename and not meta.get("source_filename"):
        meta["source_filename"] = project.source_filename


def set_input_file(meta: dict[str, Any], path: str) -> None:
    meta["input_file"] = path


def append_image(meta: dict[str, Any], image_name: str) -> None:
    images: list[str] = list(meta.get("images") or [])
    if image_name not in images:
        images.append(image_name)
    meta["images"] = images


def set_outputs(meta: dict[str, Any], *, docx_path: str, pdf_path: str | None = None) -> None:
    meta["output_file"] = docx_path
    if pdf_path:
        meta["output_pdf"] = pdf_path


def add_error(meta: dict[str, Any], message: str) -> None:
    errors: list[str] = list(meta.get("errors") or [])
    errors.append(message)
    meta["errors"] = errors


def topic_value(meta: dict[str, Any], fallback: str = "лабораторной работы") -> str:
    return (meta.get("topic") or "").strip() or fallback
