from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class RunModel(BaseModel):
    id: str
    text: str
    font_name: Optional[str] = None
    font_size_pt: Optional[float] = None
    bold: Optional[bool] = None
    italic: Optional[bool] = None


class ParagraphModel(BaseModel):
    id: str
    text: str
    style_name: Optional[str] = None
    alignment: Optional[str] = None
    first_line_indent_cm: Optional[float] = None
    line_spacing: Optional[float] = None
    space_before_pt: Optional[float] = None
    space_after_pt: Optional[float] = None
    block_type: Optional[str] = None
    runs: List[RunModel] = Field(default_factory=list)


class SectionModel(BaseModel):
    id: str
    left_margin_cm: Optional[float] = None
    right_margin_cm: Optional[float] = None
    top_margin_cm: Optional[float] = None
    bottom_margin_cm: Optional[float] = None


class DocumentModel(BaseModel):
    paragraphs: List[ParagraphModel] = Field(default_factory=list)
    sections: List[SectionModel] = Field(default_factory=list)
