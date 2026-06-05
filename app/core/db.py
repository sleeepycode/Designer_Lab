from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


def _sqlite_path(url: str) -> Path | None:
    if not url.startswith('sqlite'):
        return None
    # sqlite:///./file.db или sqlite:////abs/path.db
    raw = url.removeprefix('sqlite:///')
    if not raw or raw == ':memory:':
        return None
    if raw.startswith('/'):
        return Path(raw)
    return Path(raw)


def _engine_kwargs() -> dict:
    url = settings.database_url
    kwargs: dict = {}
    if url.startswith('sqlite'):
        kwargs['connect_args'] = {'check_same_thread': False}
        db_path = _sqlite_path(url)
        if db_path is not None:
            db_path.parent.mkdir(parents=True, exist_ok=True)
    return kwargs


engine = create_engine(settings.database_url, **_engine_kwargs())
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Создать таблицы, если их ещё нет (SQLite: без отдельного сервера и alembic)."""
    import app.models.project  # noqa: F401
    import app.models.task  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)


def check_db_connection() -> None:
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
