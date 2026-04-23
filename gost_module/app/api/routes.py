from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.engine.document_engine import (
    apply_fix,
    create_and_analyze,
    export_document,
    get_issues,
    undo_last,
)
from app.models.api import ApplyFixRequest, UndoRequest

router = APIRouter()


@router.post('/analyze')
async def analyze(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Поддерживаются только файлы .docx')

    with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        return create_and_analyze(str(tmp_path))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post('/apply-fix')
def apply_fix_route(payload: ApplyFixRequest):
    try:
        return apply_fix(payload.document_id, payload.fix_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post('/undo')
def undo_route(payload: UndoRequest):
    try:
        return undo_last(payload.document_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get('/document/{document_id}/issues')
def get_document_issues(document_id: str):
    try:
        return get_issues(document_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get('/document/{document_id}/download')
def download_document(document_id: str):
    try:
        export_path = export_document(document_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        path=export_path,
        filename=Path(export_path).name,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )
