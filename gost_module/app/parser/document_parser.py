from __future__ import annotations

from app.models.document import DocumentModel
from app.parser.paragraph_parser import parse_paragraphs
from app.parser.section_parser import parse_sections


def parse_document(doc) -> DocumentModel:
    return DocumentModel(
        paragraphs=parse_paragraphs(doc),
        sections=parse_sections(doc),
    )
