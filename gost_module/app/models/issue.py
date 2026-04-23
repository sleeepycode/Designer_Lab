from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class IssueModel(BaseModel):
    issue_id: str
    rule_id: str
    severity: str
    message: str
    explanation: str
    paragraph_id: Optional[str] = None
    run_id: Optional[str] = None
    preview: Optional[str] = None
    actual: Optional[str] = None
    expected: Optional[str] = None
    can_auto_apply: bool = False
    fix_id: Optional[str] = None
