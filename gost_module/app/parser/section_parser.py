from __future__ import annotations

from app.models.document import SectionModel
from app.utils.units import emu_to_cm


def parse_sections(doc) -> list[SectionModel]:
    sections = []
    for i, section in enumerate(doc.sections):
        sections.append(
            SectionModel(
                id=f's_{i}',
                left_margin_cm=emu_to_cm(section.left_margin),
                right_margin_cm=emu_to_cm(section.right_margin),
                top_margin_cm=emu_to_cm(section.top_margin),
                bottom_margin_cm=emu_to_cm(section.bottom_margin),
            )
        )
    return sections
