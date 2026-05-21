"""
Стили для DOCX документов по ГОСТ (с использованием встроенных стилей Word)
"""

import logging
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from app.core.config import settings

logger = logging.getLogger(__name__)


def set_run_font(run, font_name=None, size_pt=None, bold=False, italic=False, color_rgb=None):
    """
    Устанавливает шрифт для run
    """
    font_name = font_name or settings.font_name
    size_pt = size_pt or settings.font_size_pt
    
    run.font.name = font_name
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    
    if color_rgb:
        run.font.color.rgb = color_rgb
    
    # Для поддержки кириллицы
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)


def setup_document_styles(doc: Document) -> Document:
    """
    Настраивает встроенные стили документа
    
    Используются стандартные стили Word:
    - Heading 1: заголовки разделов (центр, жирный, СИНИЙ)
    - Normal: основной текст (красная строка, по ширине)
    - Normal: для библиографии (с отступом)
    - Caption: для подписей
    """
    
    heading_style = doc.styles['Heading 1']
    heading_style.font.name = settings.font_name
    heading_style.font.size = Pt(settings.font_size_pt)
    heading_style.font.bold = True
    heading_style.font.color.rgb = RGBColor(0, 0, 0)
    heading_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading_style.paragraph_format.space_before = Pt(0)
    heading_style.paragraph_format.space_after = Pt(0)
    heading_style.paragraph_format.line_spacing = settings.line_spacing
    logger.debug("Configured style: Heading 1 (blue color)")
    
    normal_style = doc.styles['Normal']
    normal_style.font.name = settings.font_name
    normal_style.font.size = Pt(settings.font_size_pt)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    normal_style.paragraph_format.first_line_indent = Cm(settings.first_line_indent_cm)
    normal_style.paragraph_format.line_spacing = settings.line_spacing
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.space_after = Pt(0)
    logger.debug("Configured style: Normal")
    
    list_style = doc.styles['List Number']
    list_style.font.name = settings.font_name
    list_style.font.size = Pt(settings.font_size_pt)
    list_style.paragraph_format.left_indent = Cm(1.25)
    list_style.paragraph_format.first_line_indent = Cm(0)
    list_style.paragraph_format.line_spacing = settings.line_spacing
    logger.debug("Configured style: List Number")
    
    if 'Caption' in doc.styles:
        caption_style = doc.styles['Caption']
        caption_style.font.name = settings.font_name
        caption_style.font.size = Pt(12)
        caption_style.font.italic = True
        caption_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption_style.paragraph_format.space_before = Pt(6)
        caption_style.paragraph_format.space_after = Pt(6)
        logger.debug("Configured style: Caption")
    
    return doc


def add_heading_center(doc: Document, text: str) -> None:
    """
    Добавляет заголовок с использованием стиля Heading 1 (синий цвет)
    """
    heading = doc.add_heading(text, level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_gost_paragraph(doc: Document, text: str) -> None:
    """
    Добавляет абзац с использованием стиля Normal
    """
    if text.strip():
        doc.add_paragraph(text.strip())


def add_bibliography_item(doc: Document, number: int, reference: str) -> None:
    """
    Добавляет элемент списка литературы с использованием стиля List Number
    """
    paragraph = doc.add_paragraph(f"{number}. {reference}", style='List Number')


def add_caption(doc: Document, text: str, is_figure: bool = True) -> None:
    """
    Добавляет подпись к рисунку или таблице
    """
    paragraph = doc.add_paragraph(text, style='Caption')