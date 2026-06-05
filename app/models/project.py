import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ProjectStatus(str, enum.Enum):
    UPLOADED = "uploaded"      # файл загружен
    PROCESSING = "processing"  # оркестрация: валидация, doc-service (не ML)
    ANALYZING = "analyzing"    # документ/данные у ML
    READY = "ready"
    ERROR = "error"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            values_callable=lambda e: [item.value for item in e],
            name='project_status',
            native_enum=False,
        ),
        default=ProjectStatus.UPLOADED,
        nullable=False,
    )
    source_filename: Mapped[str] = mapped_column(String, nullable=False)
    source_path: Mapped[str] = mapped_column(String, nullable=False)
    metadata_path: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
