from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


def _engine_kwargs() -> dict:
    url = settings.database_url
    if url.startswith('sqlite'):
        return {'connect_args': {'check_same_thread': False}}
    return {}


engine = create_engine(settings.database_url, **_engine_kwargs())
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Создать таблицы, если их ещё нет (удобно при sqlite без alembic)."""
    import app.models.project  # noqa: F401
    import app.models.task  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
