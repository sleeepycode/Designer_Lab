import logging
from pathlib import Path
from typing import Dict, Any
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx2pdf import convert as docx_to_pdf
import json
from app.services.docx_core import ensure_project_dir, save_json
from app.services.gost_applier import apply_gost_formatting
from app.services.title_page_generator import generate_title_page
from app.core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def apply_ml_changes_to_structure(
    original_structure: Dict[str, Any],
    ml_response: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Применяет правки ML к структуре.
    """
    logger.info("=" * 50)
    logger.info("Applying ML changes to structure")
    logger.debug(f"ML Response: {json.dumps(ml_response, ensure_ascii=False, indent=2)[:1000]}")
    
    result = {
        'paragraphs': original_structure.get('paragraphs', []),
        'tables': original_structure.get('tables', []),
        'images': original_structure.get('images', []),
        'content_blocks': original_structure.get('content_blocks', []),
    }
    
    generated_sections = []
    
    if 'generated_sections' in ml_response:
        generated_sections = ml_response['generated_sections']
        logger.info(f"Found 'generated_sections' at root: {len(generated_sections)} sections")
    elif 'report' in ml_response and 'generated_sections' in ml_response['report']:
        generated_sections = ml_response['report']['generated_sections']
        logger.info(f"Found 'generated_sections' in 'report': {len(generated_sections)} sections")
    else:
        logger.warning(f"No 'generated_sections' found in ml_response")
        logger.debug(f"Available keys: {list(ml_response.keys())}")
    
    for section in generated_sections:
        section_key = section.get('section')
        section_text = section.get('text', '')
        section_title = section.get('title', '')
        
        logger.debug(f"Processing section: {section_key}")
        logger.debug(f"  Title: {section_title[:50]}...")
        logger.debug(f"  Text length: {len(section_text)} chars")
        
        if section_key:
            result[section_key] = {
                'type': 'section',
                'title': section_title,
                'content': section_text,
                'source': 'ml'
            }
            logger.info(f"Added to result: {section_key}")
    
    bibliography = []
    if 'bibliography' in ml_response:
        bibliography = ml_response['bibliography']
        logger.info(f"Found 'bibliography' at root: {len(bibliography)} items")
    elif 'report' in ml_response and 'bibliography' in ml_response['report']:
        bibliography = ml_response['report']['bibliography']
        logger.info(f"Found 'bibliography' in 'report': {len(bibliography)} items")
    
    if bibliography:
        result['bibliography'] = bibliography
        for i, ref in enumerate(bibliography):
            logger.debug(f"  Bibliography {i+1}: {ref[:50]}...")
    
    logger.info(f"Final result keys: {list(result.keys())}")
    logger.info("=" * 50)
    
    return result


def build_document_from_structured_data(structure: Dict[str, Any], output_path: str) -> str:
    """
    Собирает DOCX из структурированных данных
    """
    logger.info("=" * 50)
    logger.info("BUILDING DOCUMENT FROM STRUCTURE")
    logger.debug(f"Structure keys: {list(structure.keys())}")
    
    # Проверяем наличие ML-секций
    for section_key in ['introduction', 'theory', 'practice', 'conclusion']:
        if section_key in structure:
            section_data = structure[section_key]
            logger.info(f"Found section '{section_key}':")
            logger.debug(f"  Title: {section_data.get('title', 'no title')}")
            logger.debug(f"  Content length: {len(section_data.get('content', ''))} chars")
            content_preview = section_data.get('content', '')[:200]
            if content_preview:
                logger.debug(f"  Content preview: {content_preview}...")
        else:
            logger.debug(f"Section '{section_key}' NOT found in structure")
    
    doc = Document()
    
    # Настройка стилей
    style = doc.styles['Normal']
    style.font.name = settings.font_name
    style.font.size = Pt(settings.font_size_pt)
    logger.debug(f"Document styles configured: font={settings.font_name}, size={settings.font_size_pt}pt")
    
    # Порядок секций
    section_order = ['introduction', 'theory', 'practice', 'conclusion']
    section_titles = {
        'introduction': 'Введение',
        'theory': 'Теоретическая часть',
        'practice': 'Практическая часть',
        'conclusion': 'Заключение'
    }
    
    added_count = 0
    
    # Добавляем секции от ML
    for section_key in section_order:
        section = structure.get(section_key)
        if section and isinstance(section, dict):
            title = section.get('title', section_titles.get(section_key, section_key))
            content = section.get('content', '')
            
            if content.strip():
                doc.add_heading(title, level=1)
                logger.debug(f"Added heading: {title}")
                
                para_count = 0
                for para in content.split('\n'):
                    if para.strip():
                        p = doc.add_paragraph(para.strip())
                        p.paragraph_format.first_line_indent = Cm(settings.first_line_indent_cm)
                        p.paragraph_format.line_spacing = settings.line_spacing
                        para_count += 1
                
                added_count += 1
                logger.info(f"Added section '{section_key}' with {len(content)} chars ({para_count} paragraphs)")
            else:
                logger.warning(f"Section '{section_key}' has empty content, skipping")
        else:
            logger.debug(f"Section '{section_key}' not found or not a dict")
    
    logger.info(f"Total ML sections added: {added_count}")
    
    # Добавляем библиографию
    bibliography = structure.get('bibliography', [])
    if bibliography:
        doc.add_heading('Список литературы', level=1)
        logger.debug("Added bibliography heading")
        
        for i, ref in enumerate(bibliography):
            p = doc.add_paragraph(ref)
            p.style = 'List Number'
            logger.debug(f"  Bibliography item {i+1}: {ref[:50]}...")
        
        logger.info(f"Added bibliography with {len(bibliography)} items")
    else:
        logger.debug("No bibliography found in structure")
    
    # Сохраняем документ
    try:
        doc.save(output_path)
        logger.info(f"Document saved successfully to: {output_path}")
        
        # Проверяем размер файла
        file_size = Path(output_path).stat().st_size
        logger.debug(f"Output file size: {file_size} bytes")
        
    except Exception as e:
        logger.error(f"Failed to save document: {str(e)}")
        raise
    
    logger.info("=" * 50)
    
    return output_path


def assemble_full_document(
    project_id: str,
    ml_response: Dict[str, Any],
    title_page_data: Dict[str, Any],
    output_filename: str = None
) -> Dict[str, Any]:
    """
    Полный пайплайн сборки документа
    """
    logger.info("=" * 50)
    logger.info(f"Starting full document assembly for project: {project_id}")
    
    project_dir = ensure_project_dir(project_id)
    extracted_path = project_dir / 'extract_response.json'
    
    if not extracted_path.exists():
        error_msg = f'Extracted data not found for project {project_id} at {extracted_path}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}
    
    logger.debug(f"Loading extracted structure from: {extracted_path}")
    
    # Загружаем исходную структуру
    with open(extracted_path, 'r', encoding='utf-8') as f:
        original_structure = json.load(f)
    
    logger.debug(f"Original structure has {len(original_structure.get('paragraphs', []))} paragraphs, "
                f"{len(original_structure.get('images', []))} images")
    
    # Применяем ML-правки
    merged_structure = apply_ml_changes_to_structure(original_structure, ml_response)
    
    # Сохраняем объединённую структуру
    merged_path = project_dir / 'merged_structure.json'
    save_json(merged_path, merged_structure)
    logger.debug(f"Merged structure saved to: {merged_path}")
    
    # Определяем имена файлов (используем output_filename если передан)
    if output_filename:
        # Если передан полный путь с расширением
        if output_filename.endswith('.docx'):
            temp_docx = project_dir / output_filename.replace('_final.docx', '_temp.docx')
            gost_docx = project_dir / output_filename.replace('_final.docx', '_gost.docx')
            final_docx = project_dir / output_filename
        else:
            temp_docx = project_dir / f'{output_filename}_temp.docx'
            gost_docx = project_dir / f'{output_filename}_gost.docx'
            final_docx = project_dir / f'{output_filename}.docx'
    else:
        temp_docx = project_dir / f'{project_id}_temp.docx'
        gost_docx = project_dir / f'{project_id}_gost.docx'
        final_docx = project_dir / f'{project_id}_final.docx'
    
    logger.debug(f"Temp file: {temp_docx}")
    logger.debug(f"GOST file: {gost_docx}")
    logger.debug(f"Final file: {final_docx}")
    
    # Собираем временный DOCX
    logger.info("Building temporary document...")
    build_document_from_structured_data(merged_structure, str(temp_docx))
    
    # Проверяем, создался ли временный файл
    if not temp_docx.exists():
        error_msg = f'Temp file not created: {temp_docx}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}
    
    logger.info(f"Temp file created: {temp_docx.stat().st_size} bytes")
    
    # Применяем ГОСТ форматирование
    logger.info("Applying GOST formatting...")
    apply_gost_formatting(str(temp_docx), str(gost_docx))
    
    # Проверяем, создался ли GOST файл
    if not gost_docx.exists():
        error_msg = f'GOST file not created: {gost_docx}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}
    
    logger.info(f"GOST file created: {gost_docx.stat().st_size} bytes")
    
    # Добавляем титульный лист
    logger.info("Adding title page...")
    generate_title_page(
        input_path=str(gost_docx),
        output_path=str(final_docx),
        department=title_page_data.get('department', ''),
        discipline=title_page_data.get('discipline', ''),
        lab_number=title_page_data.get('lab_number', ''),
        lab_title=title_page_data.get('lab_title', ''),
        student_name=title_page_data.get('student_name', ''),
        student_group=title_page_data.get('student_group', ''),
        reviewer_name=title_page_data.get('reviewer_name', ''),
    )
    
    # Проверяем, создался ли финальный файл
    if not final_docx.exists():
        error_msg = f'Final file not created: {final_docx}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}
    
    logger.info(f"Final file created: {final_docx.stat().st_size} bytes")
    
    # Очищаем временные файлы
    temp_docx.unlink(missing_ok=True)
    gost_docx.unlink(missing_ok=True)
    logger.debug("Temporary files cleaned up")
    
    logger.info(f"Assembly completed successfully for project {project_id}")
    logger.info("=" * 50)
    
    return {
        'status': 'completed',
        'output_path': str(final_docx),
        'project_id': project_id
    }


def convert_docx_to_pdf(docx_path: str, pdf_path: str) -> bool:
    """
    Конвертирует DOCX в PDF
    
    Args:
        docx_path: путь к DOCX файлу
        pdf_path: путь для сохранения PDF
    
    Returns:
        True если успешно, False если ошибка
    """
    try:
        logger.info(f"Converting DOCX to PDF: {docx_path} -> {pdf_path}")
        docx_to_pdf(docx_path, pdf_path)
        
        if Path(pdf_path).exists():
            logger.info(f"PDF created successfully: {pdf_path} ({Path(pdf_path).stat().st_size} bytes)")
            return True
        else:
            logger.error(f"PDF file not created: {pdf_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to convert DOCX to PDF: {str(e)}")
        return False