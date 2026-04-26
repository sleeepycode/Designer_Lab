from pathlib import Path
import shutil
import json
from fastapi import UploadFile

from app.core.config import settings, ensure_dirs


def save_input_file(task_id: str, upload_file: UploadFile) -> str:
    ensure_dirs()
    ext = Path(upload_file.filename).suffix.lower()
    path = Path(settings.input_dir) / f'{task_id}{ext}'
    with path.open('wb') as f:
        shutil.copyfileobj(upload_file.file, f)
    return str(path)


def get_output_path(task_id: str) -> str:
    ensure_dirs()
    return str(Path(settings.output_dir) / f'{task_id}.docx')


def get_report_path(task_id: str) -> str:
    ensure_dirs()
    return str(Path(settings.report_dir) / f'{task_id}.json')


ALLOWED_PROJECT_EXTENSIONS = {".docx", ".pdf", ".png", ".jpg", ".jpeg"}


def get_project_root(project_id: str) -> Path:
    ensure_dirs()
    return Path(settings.projects_dir) / project_id


def ensure_project_dirs(project_id: str) -> dict[str, Path]:
    root = get_project_root(project_id)
    input_dir = root / "input"
    images_dir = root / "images"
    output_dir = root / "output"
    for path in [root, input_dir, images_dir, output_dir]:
        path.mkdir(parents=True, exist_ok=True)
    return {"root": root, "input": input_dir, "images": images_dir, "output": output_dir}


def save_project_source_file(project_id: str, upload_file: UploadFile) -> str:
    ext = Path(upload_file.filename).suffix.lower()
    if ext not in ALLOWED_PROJECT_EXTENSIONS:
        raise ValueError("Неподдерживаемый формат файла.")

    dirs = ensure_project_dirs(project_id)
    target_dir = dirs["images"] if ext in {".png", ".jpg", ".jpeg"} else dirs["input"]
    safe_name = Path(upload_file.filename).name
    path = target_dir / safe_name
    with path.open("wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return str(path)


def write_project_metadata(project_id: str, metadata: dict) -> str:
    dirs = ensure_project_dirs(project_id)
    metadata_path = dirs["root"] / "metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    return str(metadata_path)


def read_project_metadata(project_id: str) -> dict:
    dirs = ensure_project_dirs(project_id)
    metadata_path = dirs["root"] / "metadata.json"
    if not metadata_path.exists():
        return {}
    with metadata_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_project_output_file(project_id: str, task_id: str, output_source_path: str) -> str:
    dirs = ensure_project_dirs(project_id)
    source = Path(output_source_path)
    if not source.exists():
        raise FileNotFoundError("Исходный output-файл задачи не найден.")
    target = dirs["output"] / f"{task_id}.docx"
    shutil.copy2(source, target)
    return str(target)
