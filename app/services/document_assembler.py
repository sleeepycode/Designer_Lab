import logging
from pathlib import Path
from typing import Dict, Any
from docx import Document
from docx2pdf import convert as docx_to_pdf
import json

from docx.shared import Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.services.docx_core import ensure_project_dir, save_json
from app.services.gost_applier import apply_gost_formatting
from app.services.title_page_generator import generate_title_page
from app.services.styles import *

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
    Применяет правки ML к структуре, сохраняя изображения и их подписи
    """
    logger.info("=" * 50)
    logger.info("Applying ML changes to structure")
    
    result = {
        'paragraphs': original_structure.get('paragraphs', []),
        'tables': original_structure.get('tables', []),
        'images': original_structure.get('images', []),
        'content_blocks': original_structure.get('content_blocks', []),
        '_ml_response': ml_response,
    }
    
    generated_sections = []
    
    if 'generated_sections' in ml_response:
        generated_sections = ml_response['generated_sections']
    elif 'report' in ml_response and 'generated_sections' in ml_response['report']:
        generated_sections = ml_response['report']['generated_sections']
    
    ml_sections = {}
    for section in generated_sections:
        section_key = section.get('section')
        if section_key:
            ml_sections[section_key] = {
                'title': section.get('title', ''),
                'content': section.get('text', ''),
                'source': section.get('source', 'ml')
            }
            logger.info(f"ML will replace section: {section_key}")
    
    if result.get('content_blocks'):
        result['content_blocks'] = merge_ml_into_content_blocks(
            result['content_blocks'],
            ml_sections
        )
    
    if 'images' in ml_response:
        ml_images = {img.get('image_id'): img for img in ml_response['images'] if img.get('image_id')}
        
        for img in result['images']:
            img_id = img.get('id')
            if img_id in ml_images:
                ml_img = ml_images[img_id]
                new_caption = ml_img.get('caption')
                if new_caption:
                    img['caption'] = new_caption
                    logger.debug(f"Updated caption for {img_id}: {new_caption[:50]}...")
        
        for block in result.get('content_blocks', []):
            if block.get('type') == 'image':
                img_data = block.get('data', {})
                img_id = img_data.get('id')
                if img_id in ml_images:
                    new_caption = ml_images[img_id].get('caption')
                    if new_caption:
                        img_data['caption'] = new_caption
                        logger.debug(f"Updated caption in content_blocks for {img_id}")
    
    bibliography = []
    if 'bibliography' in ml_response:
        bibliography = ml_response['bibliography']
    elif 'report' in ml_response and 'bibliography' in ml_response['report']:
        bibliography = ml_response['report']['bibliography']
    
    if bibliography:
        result['bibliography'] = bibliography
    
    for section_key, section_data in ml_sections.items():
        result[section_key] = {
            'type': 'section',
            'title': section_data['title'],
            'content': section_data['content'],
            'source': 'ml'
        }
    
    return result


def update_content_blocks_with_ml(
    content_blocks: list[Dict[str, Any]],
    ml_sections: Dict[str, Any],
    original_images: list[Dict[str, Any]]
) -> list[Dict[str, Any]]:
    """
    Обновляет content_blocks, заменяя текст секций на ML-версии,
    но сохраняя все изображения на своих местах
    """
    if not content_blocks:
        result = []
        for img in original_images:
            result.append({
                'type': 'image',
                'data': img
            })
        return result
    
    result = []
    
    section_keywords = {
        'introduction': ['введение', 'цель работы'],
        'theory': ['теоретическая часть', 'теория'],
        'practice': ['практическая часть', 'ход работы'],
        'conclusion': ['вывод', 'заключение', 'итог']
    }
    
    current_section = None
    section_content_buffer = []
    
    for block in content_blocks:
        block_type = block.get('type')
        
        if block_type == 'image':
            result.append(block)
            logger.debug(f"Preserved image block: {block.get('data', {}).get('id', 'unknown')}")
            
        elif block_type == 'paragraph':
            text = block.get('data', {}).get('text', '')
            text_lower = text.lower()
            
            detected_section = None
            for section_key, keywords in section_keywords.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        detected_section = section_key
                        break
                if detected_section:
                    break
            
            if detected_section and detected_section in ml_sections:
                if section_content_buffer:
                    for buffered_text in section_content_buffer:
                        result.append({
                            'type': 'paragraph',
                            'data': {'text': buffered_text}
                        })
                    section_content_buffer = []
                
                ml_data = ml_sections[detected_section]
                result.append({
                    'type': 'paragraph',
                    'data': {'text': ml_data.get('title', section_keywords[detected_section][0])}
                })
                
                new_content = ml_data.get('content', '')
                for para in new_content.split('\n'):
                    if para.strip():
                        result.append({
                            'type': 'paragraph',
                            'data': {'text': para.strip()}
                        })
                
                logger.info(f"Replaced section '{detected_section}' with ML content")
                current_section = None
                
            else:
                is_section_content = False
                for section_key in section_keywords:
                    if current_section == section_key:
                        is_section_content = True
                        break
                
                if is_section_content and current_section not in ml_sections:
                    section_content_buffer.append(text)
                else:
                    if section_content_buffer:
                        for buffered_text in section_content_buffer:
                            result.append({
                                'type': 'paragraph',
                                'data': {'text': buffered_text}
                            })
                        section_content_buffer = []
                    result.append(block)
        
        elif block_type == 'table':
            result.append(block)
    
    if section_content_buffer:
        for buffered_text in section_content_buffer:
            result.append({
                'type': 'paragraph',
                'data': {'text': buffered_text}
            })
    
    return result


def extract_sections_from_paragraphs(paragraphs: list) -> Dict[str, str]:

    sections = {
        'introduction': '',
        'theory': '',
        'practice': '',
        'conclusion': ''
    }

    current_section = None

    section_patterns = [
        ('introduction', 'введение'),
        ('introduction', 'цель работы'),
        ('introduction', 'цель лабораторной работы'),

        ('theory', 'теоретическая часть'),
        ('theory', 'теоретические сведения'),
        ('theory', 'теория'),

        ('practice', 'практическая часть'),
        ('practice', 'ход работы'),
        ('practice', 'выполнение работы'),
        ('practice', 'экспериментальная часть'),

        ('conclusion', 'заключение'),
        ('conclusion', 'выводы'),
        ('conclusion', 'вывод'),
    ]

    def detect_section(text: str) -> str | None:
        text_lower = text.lower().strip()

        for section_key, keyword in section_patterns:
            if keyword in text_lower:
                return section_key

        return None

    def is_header(text: str) -> bool:
        if len(text) > 100:
            return False

        text_lower = text.lower()

        for _, keyword in section_patterns:
            if keyword in text_lower:
                return True

        return False

    for para in paragraphs:
        text = para.get('text', '') if isinstance(para, dict) else str(para)

        if not text.strip():
            continue

        if is_header(text):
            detected = detect_section(text)

            if detected:
                current_section = detected
                logger.debug(f"Section header detected: '{text[:50]}...' -> {current_section}")

            continue

        if current_section and text.strip():
            if sections[current_section]:
                sections[current_section] += '\n' + text
            else:
                sections[current_section] = text

    for key, value in sections.items():
        if value:
            logger.debug(f"Section '{key}': {len(value)} chars")
        else:
            logger.debug(f"Section '{key}': empty")

    return sections


def add_images_to_document(doc: Document, structure: Dict[str, Any]) -> None:
    images = structure.get("images", [])

    if not images:
        logger.info("No images found in structure")
        return

    logger.info(f"Adding {len(images)} images to document")

    for index, image in enumerate(images, start=1):
        image_path = (
            image.get("local_path")
            or image.get("path")
            or ""
        )

        if not image_path:
            logger.warning(f"Image {index} has no path, skipping")
            continue

        if image_path.startswith("http://") or image_path.startswith("https://"):
            logger.warning(f"Image {index} has URL only, skipping: {image_path}")
            continue

        image_path = image_path.replace("\\", "/")
        path = Path(image_path)

        if not path.exists():
            logger.warning(f"Image file not found, skipping: {path}")
            continue

        try:
            paragraph = doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

            run = paragraph.add_run()
            run.add_picture(str(path), width=Cm(12))

            caption_text = (
                image.get("caption")
                or f"Рисунок {index} — Иллюстрация к отчёту"
            )

            caption = doc.add_paragraph(caption_text)
            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER

            logger.info(f"Added image {index}: {path}")

        except Exception as exc:
            logger.error(f"Failed to add image {index}: {path}; error={exc}")


def build_document_from_structured_data(structure: Dict[str, Any], output_path: str) -> str:
    """
    Собирает DOCX из content_blocks с правильными позициями изображений и подписями по ГОСТ
    """
    logger.info("=" * 50)
    logger.info("BUILDING DOCUMENT FROM STRUCTURE")
    
    doc = Document()
    doc = setup_document_styles(doc)
    
    ml_images_captions = {}
    ml_response = structure.get('_ml_response', {})
    
    if 'images' in ml_response:
        for ml_img in ml_response['images']:
            image_id = ml_img.get('image_id', '')
            caption = ml_img.get('caption', '')
            if image_id and caption:
                ml_images_captions[image_id] = caption
                logger.debug(f"Found ML caption for {image_id}: {caption[:50]}...")
    
    content_blocks = structure.get('content_blocks', [])
    
    if not content_blocks:
        logger.warning("No content_blocks found, using fallback")
        content_blocks = build_content_blocks_from_fallback(structure)
    
    for block in content_blocks:
        block_type = block.get('type')
        data = block.get('data', {})
        
        if block_type == 'paragraph':
            text = data.get('text', '')
            if text.strip():
                text_lower = text.lower()
                is_heading = any(
                    keyword in text_lower 
                    for keywords in [['введение', 'теоретическая', 'практическая', 'вывод', 'заключение']]
                    for keyword in keywords
                ) and len(text) < 100
                
                if is_heading:
                    add_heading_center(doc, text)
                else:
                    p = doc.add_paragraph(text.strip())
                    p.paragraph_format.first_line_indent = Cm(settings.first_line_indent_cm)
                    p.paragraph_format.line_spacing = settings.line_spacing
                    
        elif block_type == 'image':
            image_path = data.get('path', '')
            image_id = data.get('id', '')
            original_caption = data.get('caption', '')
            
            caption = ml_images_captions.get(image_id, original_caption)
            
            if image_path and Path(image_path).exists():
                try:
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run()
                    run.add_picture(image_path, width=Cm(12))
                    logger.debug(f"Inserted image: {Path(image_path).name}")
                    
                    if caption:
                        cap = doc.add_paragraph(caption)
                        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        cap.paragraph_format.space_before = Pt(6)
                        cap.paragraph_format.space_after = Pt(6)
                        cap.paragraph_format.line_spacing = 1.0
                        
                        for run in cap.runs:
                            run.font.name = settings.font_name
                            run.font.size = Pt(settings.font_size_pt)
                            run.font.italic = True
                            run.font.bold = False
                        logger.debug(f"Added GOST caption: {caption[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Failed to insert image: {e}")
                    doc.add_paragraph(f"[Изображение: {Path(image_path).name}]")
                    
        elif block_type == 'table':
            rows = data.get('rows', [])
            if rows:
                table = doc.add_table(rows=len(rows), cols=len(rows[0]) if rows else 1)
                table.style = 'Table Grid'
                for i, row in enumerate(rows):
                    for j, cell_text in enumerate(row):
                        table.cell(i, j).text = str(cell_text)
    
    bibliography = structure.get('bibliography', [])
    if bibliography:
        add_heading_center(doc, 'Список литературы')
        for i, ref in enumerate(bibliography):
            add_bibliography_item(doc, i + 1, ref)
    
    doc.save(output_path)
    logger.info(f"Document saved to: {output_path}")
    
    return output_path


def build_content_blocks_from_fallback(structure: Dict[str, Any]) -> list[Dict[str, Any]]:
    """
    Fallback: создаёт content_blocks из paragraphs и images
    """
    content_blocks = []
    
    for para in structure.get('paragraphs', []):
        content_blocks.append({
            'type': 'paragraph',
            'data': para
        })
    
    for img in structure.get('images', []):
        content_blocks.append({
            'type': 'image',
            'data': img
        })
    
    return content_blocks

def assemble_full_document(
    project_id: str,
    ml_response: Dict[str, Any],
    title_page_data: Dict[str, Any],
    output_filename: str = None
) -> Dict[str, Any]:

    logger.info("=" * 50)
    logger.info(f"Starting full document assembly for project: {project_id}")

    project_dir = ensure_project_dir(project_id)
    extracted_path = project_dir / 'extract_response.json'

    if not extracted_path.exists():
        error_msg = f'Extracted data not found for project {project_id} at {extracted_path}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}

    logger.debug(f"Loading extracted structure from: {extracted_path}")

    with open(extracted_path, 'r', encoding='utf-8') as f:
        original_structure = json.load(f)

    logger.debug(
        f"Original structure has {len(original_structure.get('paragraphs', []))} paragraphs, "
        f"{len(original_structure.get('images', []))} images"
    )

    merged_structure = apply_ml_changes_to_structure(original_structure, ml_response)

    merged_path = project_dir / 'merged_structure.json'
    save_json(merged_path, merged_structure)
    logger.debug(f"Merged structure saved to: {merged_path}")

    if output_filename:
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

    logger.info("Building temporary document...")
    build_document_from_structured_data(merged_structure, str(temp_docx))

    if not temp_docx.exists():
        error_msg = f'Temp file not created: {temp_docx}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}

    logger.info(f"Temp file created: {temp_docx.stat().st_size} bytes")

    logger.info("Applying GOST formatting...")
    apply_gost_formatting(str(temp_docx), str(gost_docx))

    if not gost_docx.exists():
        error_msg = f'GOST file not created: {gost_docx}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}

    logger.info(f"GOST file created: {gost_docx.stat().st_size} bytes")

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

    if not final_docx.exists():
        error_msg = f'Final file not created: {final_docx}'
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}

    logger.info(f"Final file created: {final_docx.stat().st_size} bytes")

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

    try:
        logger.info(f"Converting DOCX to PDF: {docx_path} -> {pdf_path}")

        docx_to_pdf(docx_path, pdf_path)

        if Path(pdf_path).exists():
            logger.info(f"PDF created successfully: {pdf_path} ({Path(pdf_path).stat().st_size} bytes)")
            return True

        logger.error(f"PDF file not created: {pdf_path}")
        return False

    except Exception as e:
        logger.error(f"Failed to convert DOCX to PDF: {str(e)}")
        return False
    

def merge_ml_into_content_blocks(
    content_blocks: list[Dict[str, Any]],
    ml_sections: Dict[str, Any]
) -> list[Dict[str, Any]]:
    """
    Внедряет ML-контент в content_blocks, сохраняя изображения на своих местах
    
    Логика:
    - Находим начало секции (заголовок)
    - Заменяем все параграфы секции на ML-контент
    - Изображения внутри секции сохраняем на тех же позициях
    """
    if not content_blocks:
        return content_blocks
    
    result = []
    
    section_start_keywords = {
        'introduction': ['введение', 'цель работы', 'цель лабораторной работы'],
        'theory': ['теоретическая часть', 'теоретические сведения', 'теория'],
        'practice': ['практическая часть', 'ход работы', 'выполнение работы'],
        'conclusion': ['вывод', 'заключение', 'выводы']
    }
    
    i = 0
    while i < len(content_blocks):
        block = content_blocks[i]
        block_type = block.get('type')
        
        section_key = None
        if block_type == 'paragraph':
            text = block.get('data', {}).get('text', '').lower()
            for key, keywords in section_start_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        section_key = key
                        break
                if section_key:
                    break
        
        if section_key and section_key in ml_sections:
            logger.info(f"Replacing section: {section_key}")
            
            ml_data = ml_sections[section_key]
            ml_title = ml_data.get('title', '')
            
            if ml_title:
                result.append({
                    'type': 'paragraph',
                    'data': {'text': ml_title}
                })
            else:
                result.append(block)
            
            i += 1
            
            section_images = []
            while i < len(content_blocks):
                next_block = content_blocks[i]
                next_type = next_block.get('type')
                
                if next_type == 'image':
                    section_images.append(next_block)
                    i += 1
                elif next_type == 'paragraph':
                    next_text = next_block.get('data', {}).get('text', '').lower()
                    is_next_section = False
                    for key, keywords in section_start_keywords.items():
                        for keyword in keywords:
                            if keyword in next_text:
                                is_next_section = True
                                break
                        if is_next_section:
                            break
                    
                    if is_next_section:
                        break
                    else:
                        i += 1
                else:
                    break
            
            ml_content = ml_data.get('content', '')
            for para in ml_content.split('\n'):
                if para.strip():
                    result.append({
                        'type': 'paragraph',
                        'data': {'text': para.strip()}
                    })
            
            for img_block in section_images:
                result.append(img_block)
                logger.debug(f"  Preserved image: {img_block.get('data', {}).get('id', 'unknown')}")
            
        else:
            result.append(block)
            i += 1
    
    return result