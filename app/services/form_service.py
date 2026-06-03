import json
from pathlib import Path
from typing import Dict, Any
from app.services.docx_core import ensure_project_dir, save_json


def save_form_data(project_id: str, form_data: Dict[str, Any]) -> Path:
    """
    Сохраняет данные формы в form.json
    """
    project_dir = ensure_project_dir(project_id)
    form_path = project_dir / 'form.json'
    save_json(form_path, form_data)
    return form_path


def get_form_data(project_id: str) -> Dict[str, Any]:
    """
    Получает данные формы из form.json
    """
    project_dir = ensure_project_dir(project_id)
    form_path = project_dir / 'form.json'
    
    if not form_path.exists():
        return {}
    
    with open(form_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_topic_from_form(project_id: str) -> str:
    """
    Извлекает topic из form.json
    topic = lab_title
    """
    form_data = get_form_data(project_id)
    return form_data.get('lab_title', '')