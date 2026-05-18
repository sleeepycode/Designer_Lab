"""
Сервис для полной сборки документа:
- Объединение исходной структуры с ML-правками
- Сборка DOCX из объединённой структуры
- Применение ГОСТ и титульного листа
"""

from pathlib import Path
from typing import Dict, Any
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.services.docx_core import ensure_project_dir, save_json
from app.services.gost_applier import apply_gost_formatting
from app.services.title_page_generator import generate_title_page
from app.core.config import settings


def apply_ml_changes_to_structure(
    original_structure: Dict[str, Any],
    ml_response: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Объединяет исходную структуру с правками ML
    """
    result = {
        'paragraphs': original_structure.get('paragraphs', []),
        'tables': original_structure.get('tables', []),
        'images': original_structure.get('images', []),
    }
    
    # Добавляем ML-секции
    sections_order = ['introduction', 'theory', 'practice', 'conclusion']
    section_titles = {
        'introduction': 'Введение',
        'theory': 'Теоретическая часть',
        'practice': 'Практическая часть / Ход работы',
        'conclusion': 'Заключение'
    }
    
    # Получаем сгенерированные секции из ML
    generated_sections = ml_response.get('generated_sections', [])
    
    for section in generated_sections:
        section_key = section.get('section')
        if section_key in sections_order:
            result[section_key] = {
                'type': 'section',
                'title': section.get('title', section_titles.get(section_key, '')),
                'content': section.get('text', ''),
                'source': 'ml_generated'
            }
    
    # Добавляем библиографию
    bibliography = ml_response.get('bibliography', [])
    if bibliography:
        result['bibliography'] = bibliography
    
    # Обрабатываем content_suggestions
    for suggestion in ml_response.get('content_suggestions', []):
        if suggestion.get('action') == 'generate':
            target = suggestion.get('target')
            if target and target not in result:
                result[target] = {
                    'type': 'section',
                    'title': suggestion.get('title', ''),
                    'content': suggestion.get('text', ''),
                    'source': 'ml_suggestion'
                }
    
    return result


def build_document_from_structured_data(structure: Dict[str, Any], output_path: str) -> str:
    """
    Собирает DOCX из структурированных данных (без ГОСТ)
    """
    doc = Document()
    
    # Устанавливаем базовые стили
    style = doc.styles['Normal']
    style.font.name = settings.font_name
    style.font.size = Pt(settings.font_size_pt)
    
    # Добавляем содержимое в правильном порядке
    # 1. Сначала исходные параграфы (но без титульного листа)
    # 2. Затем секции от ML
    # 3. В конце библиографию
    
    # Функция для добавления текста с заголовками
    def add_text_with_heading(doc: Document, text: str, is_heading: bool = False):
        if is_heading:
            doc.add_heading(text, level=1)
        else:
            p = doc.add_paragraph(text)
            p.paragraph_format.first_line_indent = Cm(settings.first_line_indent_cm)
            p.paragraph_format.line_spacing = settings.line_spacing
    
    # Добавляем исходные параграфы
    for para in structure.get('paragraphs', []):
        text = para.get('text', '') if isinstance(para, dict) else str(para)
        if text.strip():
            doc.add_paragraph(text)
    
    # Добавляем секции в определённом порядке
    section_order = ['introduction', 'theory', 'practice', 'conclusion']
    for section_key in section_order:
        section = structure.get(section_key)
        if section and isinstance(section, dict):
            # Добавляем заголовок
            doc.add_heading(section.get('title', section_key), level=1)
            # Добавляем содержимое
            content = section.get('content', '')
            if content:
                for para in content.split('\n'):
                    if para.strip():
                        doc.add_paragraph(para.strip())
    
    # Добавляем библиографию
    bibliography = structure.get('bibliography', [])
    if bibliography:
        doc.add_heading('Список литературы', level=1)
        for ref in bibliography:
            p = doc.add_paragraph(ref)
            p.style = 'List Number'
    
    # Добавляем таблицы
    for table in structure.get('tables', []):
        rows = table.get('rows', []) if isinstance(table, dict) else table
        if rows:
            tbl = doc.add_table(rows=len(rows), cols=len(rows[0]) if rows else 1)
            tbl.style = 'Table Grid'
            for i, row in enumerate(rows):
                for j, cell_text in enumerate(row):
                    tbl.cell(i, j).text = str(cell_text)
    
    doc.save(output_path)
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
    from app.services.docx_core import ensure_project_dir, save_json
    from app.services.gost_applier import apply_gost_formatting
    from app.services.title_page_generator import generate_title_page
    import json
    
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