from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.config import DOCUMENTS_DIR, EXPORTS_DIR, STATE_DIR


def _state_path(document_id: str) -> Path:
    return STATE_DIR / f"{document_id}.json"


def _doc_dir(document_id: str) -> Path:
    path = DOCUMENTS_DIR / document_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_document_record(source_path: str) -> tuple[str, Path]:
    document_id = uuid4().hex
    doc_dir = _doc_dir(document_id)
    target_path = doc_dir / 'working.docx'
    shutil.copy2(source_path, target_path)

    state = {
        'document_id': document_id,
        'working_path': str(target_path),
        'history': [],
        'issues': [],
        'fixes': {},
        'last_analysis': None,
    }
    save_state(document_id, state)
    return document_id, target_path


def save_state(document_id: str, data: dict[str, Any]) -> None:
    _state_path(document_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8'
    )


def load_state(document_id: str) -> dict[str, Any]:
    path = _state_path(document_id)
    if not path.exists():
        raise FileNotFoundError(f'State for document {document_id} not found')
    return json.loads(path.read_text(encoding='utf-8'))


def save_export(document_id: str, source_path: str) -> Path:
    export_path = EXPORTS_DIR / f'{document_id}_fixed.docx'
    shutil.copy2(source_path, export_path)
    return export_path
