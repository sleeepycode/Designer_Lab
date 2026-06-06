from __future__ import annotations

from docx import Document
from docx.shared import Pt, Cm

from app.core.config import settings


def apply_gost_formatting(docx_path: str, output_path: str) -> None:
    """
    Применяет ГОСТ параметры ко всему документу.

    :param docx_path: Путь к входному .docx файлу
    :param output_path: Путь к выходному .docx файлу
    """
    doc = Document(docx_path)

    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = settings.font_name
            run.font.size = Pt(settings.font_size_pt)

    for paragraph in doc.paragraphs:
        fmt = paragraph.paragraph_format
        fmt.line_spacing = settings.line_spacing
        fmt.first_line_indent = Cm(settings.first_line_indent_cm)
        fmt.space_before = Pt(0)
        fmt.space_after = Pt(0)

    for section in doc.sections:
        section.top_margin = Cm(settings.margin_top_cm)
        section.bottom_margin = Cm(settings.margin_bottom_cm)
        section.left_margin = Cm(settings.margin_left_cm)
        section.right_margin = Cm(settings.margin_right_cm)

    doc.save(output_path)
