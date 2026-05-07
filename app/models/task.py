import enum
import uuid
from datetime import datetime

<<<<<<< HEAD
from sqlalchemy import String, DateTime, JSON, Enum
=======
from sqlalchemy import String, DateTime, JSON, Enum, Text
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TaskStatus(str, enum.Enum):
<<<<<<< HEAD
    CREATED = 'created'
=======
    QUEUED = 'queued'
    PROCESSING = 'processing'
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    COMPLETED = 'completed'
    FAILED = 'failed'


class DocumentTask(Base):
    __tablename__ = 'document_tasks'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
<<<<<<< HEAD
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.CREATED, nullable=False)
=======
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.QUEUED, nullable=False, index=True)
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    input_path: Mapped[str] = mapped_column(String, nullable=False)
    output_path: Mapped[str | None] = mapped_column(String, nullable=True)
    report_path: Mapped[str | None] = mapped_column(String, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)
<<<<<<< HEAD
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
=======
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
