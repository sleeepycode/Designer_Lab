import enum
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class UserRole(str, enum.Enum):
    STUDENT = 'student'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            values_callable=lambda e: [item.value for item in e],
            name='user_role',
            native_enum=False,
        ),
        default=UserRole.STUDENT,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
