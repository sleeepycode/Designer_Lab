from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict
import shutil
from app.services.document_assembler import assemble_full_document

from app.services.docx_core import (
    extract_docx,
    assemble_structure,
    ensure_project_dir,
    save_json,
)

router = APIRouter(prefix='/backend2', tags=['backend2'])


@router.post('/extract')
async def extract(file: UploadFile = File(...), project_id: str | None = Form(None)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Only .docx allowed')

    # Генерируем project_id если не передан
    project_id = project_id or uuid4().hex
    project_dir = ensure_project_dir(project_id)

    # СОХРАНЯЕМ ФАЙЛ С ИМЕНЕМ project_id, а не оригинальным
    in_path = project_dir / f'{project_id}.docx'  # <-- ИСПРАВЛЕНО!
    with in_path.open('wb') as f:
        shutil.copyfileobj(file.file, f)

    # Создаём директорию для медиафайлов
    media_dir = project_dir / 'media'
    media_dir.mkdir(parents=True, exist_ok=True)

    # Извлекаем содержимое DOCX
    result = extract_docx(str(in_path), str(media_dir), project_id=project_id)
    
    # Сохраняем результат
    save_json(project_dir / 'extract_response.json', result)
    
    # Возвращаем project_id и результат
    return JSONResponse(content={
        'project_id': project_id,
        'paragraphs': result.get('paragraphs', []),
        'tables': result.get('tables', []),
        'images': result.get('images', [])
    })

@router.post('/assemble')
async def assemble(payload: Dict[str, Any] = Body(...)):
    structure = payload.get('structure')
    if not structure:
        raise HTTPException(status_code=400, detail='Request body must include structure')

    project_id = payload.get('project_id') or uuid4().hex
    project_dir = ensure_project_dir(project_id)
    ml_response = payload.get('ml_response')

    if ml_response:
        save_json(project_dir / 'ml_response.json', ml_response)

    out_path = project_dir / 'result.docx'
    res = assemble_structure(
        structure,
        str(out_path),
        project_id=project_id,
        ml_response=ml_response,
    )

    if res.get('status') != 'completed':
        raise HTTPException(status_code=500, detail=f'Assemble failed: {res.get("error")}')

    return FileResponse(
        path=str(out_path),
        filename='result.docx',
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )


@router.get('/health')
async def health():
    return {'status': 'ok'}


@router.post('/apply_ml_changes')
async def apply_ml_changes_endpoint(
    request: Request,
):
    """
    Полный пайплайн: извлечение → ML правки → сборка → ГОСТ → титульный лист
    
    Принимает JSON:
    {
        "project_id": "string",
        "ml_response": { ... },  # полный ответ от ML
        "title_page": { ... }     # данные титульного листа
    }
    
    Возвращает готовый DOCX файл
    """
    import json
    
    # Парсим JSON тело запроса
    try:
        body = await request.json()
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f'Invalid JSON: {str(e)}')
    
    # Извлекаем параметры
    project_id = body.get('project_id')
    ml_response = body.get('ml_response')
    title_page_data = body.get('title_page')
    
    # Валидация
    if not project_id:
        raise HTTPException(status_code=400, detail='project_id is required')
    if not ml_response:
        raise HTTPException(status_code=400, detail='ml_response is required')
    if not title_page_data:
        raise HTTPException(status_code=400, detail='title_page is required')
    
    # Вызываем основную логику
    result = assemble_full_document(
        project_id=project_id,
        ml_response=ml_response,
        title_page_data=title_page_data,
        output_filename=f'{project_id}_final.docx'
    )
    
    # Проверяем результат
    if result.get('status') != 'completed':
        raise HTTPException(
            status_code=500, 
            detail=result.get('error', 'Assembly failed')
        )
    
    # Возвращаем готовый файл
    return FileResponse(
        path=result['output_path'],
        filename=f'{project_id}_result.docx',
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )