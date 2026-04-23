from __future__ import annotations

from pydantic import BaseModel


class HistoryRecord(BaseModel):
    operation_id: str
    fix_id: str
    status: str
