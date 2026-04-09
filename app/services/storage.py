from pathlib import Path
import shutil
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
