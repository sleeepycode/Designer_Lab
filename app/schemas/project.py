from datetime import datetime

from pydantic import BaseModel


class ProjectUploadResponse(BaseModel):
    project_id: str
    status: str
    source_filename: str


class ProjectStatusResponse(BaseModel):
    project_id: str
    user_id: str | None = None
    status: str
    source_filename: str
    created_at: datetime
    updated_at: datetime
