from pathlib import Path
import shutil
from fastapi import UploadFile

from app.core.config import settings, ensure_dirs


def save_input_file(task_id: str, upload_file: UploadFile) -> str:
<<<<<<< HEAD
    ensure_dirs()
    ext = Path(upload_file.filename).suffix.lower()
    path = Path(settings.input_dir) / f'{task_id}{ext}'
    with path.open('wb') as f:
        shutil.copyfileobj(upload_file.file, f)
=======
    """Сохранить загруженный файл в storage/inputs"""
    ensure_dirs()
    ext = Path(upload_file.filename).suffix.lower()
    if not ext:
        ext = '.docx'
    
    path = Path(settings.input_dir) / f'{task_id}{ext}'
    
    # Прочитать содержимое файла и сохранить
    content = upload_file.file.read()
    with path.open('wb') as f:
        f.write(content)
    
    # Вернуть указатель на начало (на случай если понадобится снова)
    upload_file.file.seek(0)
    
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    return str(path)


def get_output_path(task_id: str) -> str:
    ensure_dirs()
    return str(Path(settings.output_dir) / f'{task_id}.docx')


def get_report_path(task_id: str) -> str:
    ensure_dirs()
    return str(Path(settings.report_dir) / f'{task_id}.json')
