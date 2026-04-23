from __future__ import annotations

from typing import List, Dict, Any
from pydantic import BaseModel


class AnalyzeResponse(BaseModel):
    document_id: str
    summary: Dict[str, int]
    issues: List[Dict[str, Any]]


class ApplyFixRequest(BaseModel):
    document_id: str
    fix_id: str


class UndoRequest(BaseModel):
    document_id: str
