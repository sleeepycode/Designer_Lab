from __future__ import annotations

from app.models.document import ParagraphModel, RunModel
from app.parser.classifier import classify_paragraph
from app.utils.units import emu_to_cm, safe_pt

def safe_alignment(paragraph) -> str | None:
    try:
        value = paragraph.alignment
        if value is None:
            return None
        return str(value)
    except Exception:
        pass

    try:
        ppr = paragraph._p.pPr
        if ppr is not None and ppr.jc is not None and ppr.jc.val is not None:
            raw = str(ppr.jc.val).lower()

            mapping = {
                "left": "LEFT",
                "right": "RIGHT",
                "center": "CENTER",
                "both": "JUSTIFY",
                "justify": "JUSTIFY",
                "distribute": "DISTRIBUTE",
                "start": "LEFT",
                "end": "RIGHT",
            }

            return mapping.get(raw, raw.upper())
    except Exception:
        pass

    return "UNKNOWN"

def parse_paragraphs(doc) -> list[ParagraphModel]:
    paragraphs = []

    for i, p in enumerate(doc.paragraphs):
        pf = p.paragraph_format
        runs = []

        for j, r in enumerate(p.runs):
            runs.append(
                RunModel(
                    id=f'r_{i}_{j}',
                    text=r.text,
                    font_name=r.font.name,
                    font_size_pt=safe_pt(r.font.size),
                    bold=r.bold,
                    italic=r.italic,
                )
            )

        alignment = safe_alignment(p)
        style_name = p.style.name if p.style else None
        block_type = classify_paragraph(p.text, i, style_name, alignment)

        paragraphs.append(
            ParagraphModel(
                id=f'p_{i}',
                text=p.text,
                style_name=style_name,
                alignment=alignment,
                first_line_indent_cm=emu_to_cm(pf.first_line_indent) if pf.first_line_indent is not None else None,
                line_spacing=float(pf.line_spacing) if isinstance(pf.line_spacing, (int, float)) else None,
                space_before_pt=safe_pt(pf.space_before),
                space_after_pt=safe_pt(pf.space_after),
                block_type=block_type,
                runs=runs,
            )
        )

    return paragraphs
