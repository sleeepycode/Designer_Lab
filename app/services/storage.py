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


def get_task_output_paths(task_id: str) -> dict[str, str]:
    """Пути итоговых файлов задачи: PDF и DOCX."""
    ensure_dirs()
    root = Path(settings.output_dir)
    return {
        'pdf': str(root / f'{task_id}.pdf'),
        'docx': str(root / f'{task_id}.docx'),
    }


def get_output_path(task_id: str) -> str:
    """Основной output (PDF) — для совместимости с output_path в БД."""
    return get_task_output_paths(task_id)['pdf']


def get_report_path(task_id: str) -> str:
    ensure_dirs()
    return str(Path(settings.report_dir) / f'{task_id}.json')


ALLOWED_PROJECT_INPUT_EXTENSIONS = {".docx"}
ALLOWED_PROJECT_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}


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
    dirs = ensure_project_dirs(project_id)
    if ext in ALLOWED_PROJECT_IMAGE_EXTENSIONS:
        target_dir = dirs["images"]
    elif ext in ALLOWED_PROJECT_INPUT_EXTENSIONS:
        target_dir = dirs["input"]
    else:
        raise ValueError("Неподдерживаемый формат файла.")
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


def copy_project_file_to_task_input(task_id: str, source_path: str | Path) -> str:
    ensure_dirs()
    src = Path(source_path)
    if not src.is_file():
        raise FileNotFoundError("Исходный файл не найден.")
    ext = src.suffix.lower() or ".docx"
    dest = Path(settings.input_dir) / f"{task_id}{ext}"
    shutil.copy2(src, dest)
    return str(dest)


def save_project_output_files(
    project_id: str,
    task_id: str,
    pdf_source_path: str,
    docx_source_path: str,
) -> dict[str, str]:
    dirs = ensure_project_dirs(project_id)
    out_dir = dirs['output']
    pdf_src = Path(pdf_source_path)
    docx_src = Path(docx_source_path)
    if not pdf_src.is_file():
        raise FileNotFoundError('PDF результата задачи не найден.')
    if not docx_src.is_file():
        raise FileNotFoundError('DOCX результата задачи не найден.')

    pdf_target = out_dir / f'{task_id}.pdf'
    docx_target = out_dir / f'{task_id}.docx'
    shutil.copy2(pdf_src, pdf_target)
    shutil.copy2(docx_src, docx_target)
    return {'pdf': str(pdf_target), 'docx': str(docx_target)}
