from fastapi import APIRouter, UploadFile, File, Form, Body, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict
import shutil
import json
from app.services.document_assembler import assemble_full_document, convert_docx_to_pdf
from app.services.docx_core import ensure_project_dir
from app.services.ml_client import analyze_document_with_ml
from app.services.form_service import save_form_data, get_form_data, get_topic_from_form

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

    result = extract_docx(str(in_path), str(media_dir), project_id=project_id)
    
    save_json(project_dir / 'extract_response.json', result)
    
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
    
    project_id = body.get('project_id')
    ml_response = body.get('ml_response')
    title_page_data = body.get('title_page')
    
    if not project_id:
        raise HTTPException(status_code=400, detail='project_id is required')
    if not ml_response:
        raise HTTPException(status_code=400, detail='ml_response is required')
    if not title_page_data:
        raise HTTPException(status_code=400, detail='title_page is required')
    
    result = assemble_full_document(
        project_id=project_id,
        ml_response=ml_response,
        title_page_data=title_page_data,
        output_filename=f'{project_id}_final.docx'
    )
    
    if result.get('status') != 'completed':
        raise HTTPException(
            status_code=500, 
            detail=result.get('error', 'Assembly failed')
        )
    
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
    
    possible_filenames = [
        f'{project_id}_final.docx',
        f'{project_id}_result.docx',
        f'{project_id}.docx'
    ]
    
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



@router.post('/extract-and-analyze')
async def extract_and_analyze(
    file: UploadFile = File(...),
    form_data: str = Form(...)
):
    """
    Полный пайплайн:
    1. Извлекает структуру из DOCX
    2. Сохраняет данные формы
    3. Отправляет в ML
    4. Возвращает ml_response
    """
    import json
    
    try:
        form_data_dict = json.loads(form_data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail='Invalid form_data JSON')
    
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail='Only .docx allowed')
    
    project_id = uuid4().hex
    project_dir = ensure_project_dir(project_id)
    
    in_path = project_dir / f'{project_id}.docx'
    with in_path.open('wb') as f:
        shutil.copyfileobj(file.file, f)
    
    media_dir = project_dir / 'media'
    media_dir.mkdir(parents=True, exist_ok=True)
    
    result = extract_docx(str(in_path), str(media_dir), project_id=project_id)
    save_json(project_dir / 'extract_response.json', result)
    
    save_form_data(project_id, form_data_dict)
    
    topic = form_data_dict.get('lab_title', '')
    ml_response = analyze_document_with_ml(project_id, result, topic)
    
    save_json(project_dir / 'ml_response.json', ml_response)
    
    return {
        'project_id': project_id,
        'ml_response': ml_response
    }


@router.post('/apply-ml-changes-from-storage')
async def apply_ml_changes_from_storage(
    project_id: str = Form(...)
):
    """
    Применяет сохранённые ML правки к документу
    """
    from app.services.form_service import get_form_data
    
    project_dir = ensure_project_dir(project_id)
    
    ml_response_path = project_dir / 'ml_response.json'
    if not ml_response_path.exists():
        raise HTTPException(status_code=404, detail='ml_response.json not found')
    
    with open(ml_response_path, 'r', encoding='utf-8') as f:
        ml_response = json.load(f)
    
    title_page_data = get_form_data(project_id)
    if not title_page_data:
        raise HTTPException(status_code=404, detail='form.json not found')
    
    result = assemble_full_document(
        project_id=project_id,
        ml_response=ml_response,
        title_page_data=title_page_data,
        output_filename=f'{project_id}_final.docx'
    )
    
    if result.get('status') != 'completed':
        raise HTTPException(status_code=500, detail=result.get('error', 'Assembly failed'))
    
    return FileResponse(
        path=result['output_path'],
        filename=f'{project_id}_result.docx',
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

@router.get('/debug-ml-payload/{project_id}')
async def debug_ml_payload(project_id: str):
    """
    Посмотреть payload, который Doc Service отправил в ML.
    """
    project_dir = ensure_project_dir(project_id)
    payload_path = project_dir / 'ml_request_payload.json'

    if not payload_path.exists():
        raise HTTPException(status_code=404, detail='ml_request_payload.json not found')

    with open(payload_path, 'r', encoding='utf-8') as f:
        return json.load(f)
