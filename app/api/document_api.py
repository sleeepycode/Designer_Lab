from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict
import shutil
import json
from app.services.document_assembler import assemble_full_document, convert_docx_to_pdf
from app.services.docx_core import ensure_project_dir

from app.services.docx_core import (
    extract_docx,
    ensure_project_dir,
    save_json,
)

router = APIRouter(prefix='/documents', tags=['documents'])


@router.post('/extract')
async def extract(file: UploadFile = File(...), project_id: str | None = Form(None)):
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Only .docx allowed')

    project_id = project_id or uuid4().hex
    project_dir = ensure_project_dir(project_id)

    in_path = project_dir / f'{project_id}.docx'
    with in_path.open('wb') as f:
        shutil.copyfileobj(file.file, f)

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

@router.get('/download/{project_id}')
async def download_result(
    project_id: str,
):
    """
    Скачать готовый документ по project_id
    
    Ищет файлы в порядке приоритета:
    1. {project_id}_final.docx
    2. {project_id}_result.docx  
    3. {project_id}.docx
    """
    
    project_dir = ensure_project_dir(project_id)
    
    # Возможные имена файлов (в порядке приоритета)
    possible_filenames = [
        f'{project_id}_final.docx',
        f'{project_id}_result.docx',
        f'{project_id}.docx'
    ]
    
    # Ищем первый существующий файл
    output_path = None
    for filename in possible_filenames:
        candidate = project_dir / filename
        if candidate.exists():
            output_path = candidate
            break
    
    if not output_path:
        raise HTTPException(
            status_code=404, 
            detail=f'Файл не найден. Искали: {", ".join(possible_filenames)} в {project_dir}'
        )
    
    return FileResponse(
        path=str(output_path),
        filename=f'{project_id}_result.docx',
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@router.get('/info/{project_id}')
async def get_project_info(
    project_id: str,
):
    """
    Получить информацию о проекте: какие файлы существуют
    """
    
    project_dir = ensure_project_dir(project_id)
    
    files = []
    for file in project_dir.glob('*'):
        if file.is_file():
            files.append({
                'name': file.name,
                'size': file.stat().st_size,
                'modified': file.stat().st_mtime
            })
    
    extracted_path = project_dir / 'extract_response.json'
    has_extracted = extracted_path.exists()
    
    merged_path = project_dir / 'merged_structure.json'
    has_merged = merged_path.exists()
    
    return {
        'project_id': project_id,
        'project_dir': str(project_dir),
        'has_extracted_data': has_extracted,
        'has_merged_data': has_merged,
        'files': files
    }

@router.get('/download-pdf/{project_id}')
async def download_pdf(project_id: str,):
    """
    Скачать готовый документ в формате PDF
    
    Конвертирует DOCX в PDF и возвращает файл.
    Если PDF уже существует, возвращает его.
    """
    
    project_dir = ensure_project_dir(project_id)
    
    possible_docx = [
        project_dir / f'{project_id}_final.docx',
        project_dir / f'{project_id}_result.docx',
        project_dir / f'{project_id}.docx'
    ]
    
    docx_path = None
    for candidate in possible_docx:
        if candidate.exists():
            docx_path = candidate
            break
    
    if not docx_path:
        raise HTTPException(
            status_code=404,
            detail=f'DOCX file not found for project {project_id}. Looked for: {", ".join([str(f) for f in possible_docx])}'
        )
    
    pdf_path = project_dir / f'{project_id}.pdf'
    
    if pdf_path.exists():
        docx_mtime = docx_path.stat().st_mtime
        pdf_mtime = pdf_path.stat().st_mtime
        if pdf_mtime > docx_mtime:
            return FileResponse(
                path=str(pdf_path),
                filename=f'{project_id}.pdf',
                media_type='application/pdf'
            )
    
    if not convert_docx_to_pdf(str(docx_path), str(pdf_path)):
        raise HTTPException(
            status_code=500,
            detail='Failed to convert DOCX to PDF. Check that Microsoft Word or LibreOffice is installed.'
        )
    
    return FileResponse(
        path=str(pdf_path),
        filename=f'{project_id}.pdf',
        media_type='application/pdf'
    )