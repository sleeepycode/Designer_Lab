import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column

class TaskStatus(str, enum.Enum):
    QUEUED = 'queued'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'