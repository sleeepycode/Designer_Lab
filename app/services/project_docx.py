from pathlib import Path

from app.core.config import settings
from app.models.project import Project


def resolve_primary_project_docx(project: Project) -> Path | None:
    """
    Основной DOCX для обработки: сначала исходник проекта (если это .docx),
    иначе последний по времени изменения файл из projects/{id}/input/*.docx.
    """
    root = Path(settings.projects_dir) / project.id
    if project.source_path:
        p = Path(project.source_path)
        if p.suffix.lower() == ".docx" and p.is_file():
            return p
    input_dir = root / "input"
    if input_dir.is_dir():
        docxs = [p for p in input_dir.glob("*.docx") if p.is_file()]
        if docxs:
            docxs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            return docxs[0]
    return None
