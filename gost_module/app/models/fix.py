from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class FixModel(BaseModel):
    fix_id: str
    action: str
    target_type: str
    target_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
