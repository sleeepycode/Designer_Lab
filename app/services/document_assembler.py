from pathlib import Path
from typing import Dict, Any
from docx import Document
from docx.shared import Pt, Cm
import json
from app.services.docx_core import ensure_project_dir, save_json
from app.services.gost_applier import apply_gost_formatting
from app.services.title_page_generator import generate_title_page
from app.core.config import settings


def apply_ml_changes_to_structure(
    original_structure: Dict[str, Any],
    ml_response: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Применяет правки ML к структуре.
    """

    print("=" * 50)
    print("ML_RESPONSE RECEIVED:")
    print(json.dumps(ml_response, ensure_ascii=False, indent=2)[:1000])
    print("=" * 50)
    
    result = {
        'paragraphs': original_structure.get('paragraphs', []),
        'tables': original_structure.get('tables', []),
        'images': original_structure.get('images', []),
    }
    
    generated_sections = []
    
    if 'generated_sections' in ml_response:
        generated_sections = ml_response['generated_sections']
        print(f"✅ Found 'generated_sections' at root: {len(generated_sections)} sections")
    elif 'report' in ml_response and 'generated_sections' in ml_response['report']:
        generated_sections = ml_response['report']['generated_sections']
        print(f"✅ Found 'generated_sections' in 'report': {len(generated_sections)} sections")
    else:
        print("❌ No 'generated_sections' found in ml_response")
        print(f"   Available keys: {list(ml_response.keys())}")
    
    for section in generated_sections:
        section_key = section.get('section')
        section_text = section.get('text', '')
        section_title = section.get('title', '')
        
        print(f"   Section: {section_key}")
        print(f"   Title: {section_title[:50]}...")
        print(f"   Text length: {len(section_text)} chars")
        
        if section_key:
            result[section_key] = {
                'type': 'section',
                'title': section_title,
                'content': section_text,
                'source': 'ml'
            }
            print(f"   ✅ Added to result: {section_key}")
    
    # Проверяем bibliography
    bibliography = []
    if 'bibliography' in ml_response:
        bibliography = ml_response['bibliography']
        print(f"✅ Found 'bibliography' at root: {len(bibliography)} items")
    elif 'report' in ml_response and 'bibliography' in ml_response['report']:
        bibliography = ml_response['report']['bibliography']
        print(f"✅ Found 'bibliography' in 'report': {len(bibliography)} items")
    
    if bibliography:
        result['bibliography'] = bibliography
    
    print(f"Final result keys: {list(result.keys())}")
    print("=" * 50)
    
    return result

def build_document_from_structured_data(structure: Dict[str, Any], output_path: str) -> str:
    """
    Собирает DOCX из структурированных данных
    """
    
    print("=" * 50)
    print("BUILDING DOCUMENT FROM STRUCTURE")
    print(f"Structure keys: {list(structure.keys())}")
    
    # Проверяем наличие ML-секций
    for section_key in ['introduction', 'theory', 'practice', 'conclusion']:
        if section_key in structure:
            section_data = structure[section_key]
            print(f"✅ Found section '{section_key}':")
            print(f"   Title: {section_data.get('title', 'no title')}")
            print(f"   Content length: {len(section_data.get('content', ''))} chars")
            print(f"   Content preview: {section_data.get('content', '')[:200]}...")
        else:
            print(f"❌ Section '{section_key}' NOT found in structure")
    
    doc = Document()
    
    # Настройка стилей
    style = doc.styles['Normal']
    style.font.name = settings.font_name
    style.font.size = Pt(settings.font_size_pt)
    
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
                for para in content.split('\n'):
                    if para.strip():
                        p = doc.add_paragraph(para.strip())
                        p.paragraph_format.first_line_indent = Cm(settings.first_line_indent_cm)
                        p.paragraph_format.line_spacing = settings.line_spacing
                added_count += 1
                print(f"✅ Added section '{section_key}' with {len(content)} chars")
            else:
                print(f"⚠️ Section '{section_key}' has empty content")
        else:
            print(f"⚠️ Section '{section_key}' not found or not a dict")
    
    print(f"Total sections added: {added_count}")
    
    # Добавляем библиографию
    bibliography = structure.get('bibliography', [])
    if bibliography:
        doc.add_heading('Список литературы', level=1)
        for ref in bibliography:
            p = doc.add_paragraph(ref)
            p.style = 'List Number'
        print(f"✅ Added bibliography with {len(bibliography)} items")
    
    doc.save(output_path)
    print(f"Document saved to: {output_path}")
    print("=" * 50)
    
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
    
    project_dir = ensure_project_dir(project_id)
    extracted_path = project_dir / 'extract_response.json'
    
    if not extracted_path.exists():
        return {'status': 'failed', 'error': f'Extracted data not found for project {project_id} at {extracted_path}'}
    
    # Загружаем исходную структуру
    with open(extracted_path, 'r', encoding='utf-8') as f:
        original_structure = json.load(f)
    
    # Применяем ML-правки
    merged_structure = apply_ml_changes_to_structure(original_structure, ml_response)
    
    # Сохраняем объединённую структуру
    save_json(project_dir / 'merged_structure.json', merged_structure)
    
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
    
    # Собираем временный DOCX
    build_document_from_structured_data(merged_structure, str(temp_docx))
    
    # Проверяем, создался ли временный файл
    if not temp_docx.exists():
        return {'status': 'failed', 'error': f'Temp file not created: {temp_docx}'}
    
    # Применяем ГОСТ форматирование
    apply_gost_formatting(str(temp_docx), str(gost_docx))
    
    # Проверяем, создался ли GOST файл
    if not gost_docx.exists():
        return {'status': 'failed', 'error': f'GOST file not created: {gost_docx}'}
    
    # Добавляем титульный лист
    generate_title_page(
        input_path=str(gost_docx),
        output_path=str(final_docx),
        department=title_page_data.get('department', ''),
        discipline=title_page_data.get('discipline', ''),
        lab_number=title_page_data.get('lab_number', ''),
        lab_title=title_page_data.get('lab_title', ''),
        student_group=title_page_data.get('student_group', ''),
        student_name=title_page_data.get('student_name', ''),
        reviewer_name=title_page_data.get('reviewer_name', ''),
    )
    
    # Проверяем, создался ли финальный файл
    if not final_docx.exists():
        return {'status': 'failed', 'error': f'Final file not created: {final_docx}'}
    
    # Очищаем временные файлы
    temp_docx.unlink(missing_ok=True)
    gost_docx.unlink(missing_ok=True)
    
    return {
        'status': 'completed',
        'output_path': str(final_docx),
        'project_id': project_id
    }