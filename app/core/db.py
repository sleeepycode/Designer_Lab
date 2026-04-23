from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = 'sqlite:///./lab_formatter.db'

engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_compatibility() -> None:
    """Apply minimal non-destructive SQLite schema updates for local MVP."""
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(document_tasks)"))
        columns = {row[1] for row in result}
        if "user_id" not in columns:
            conn.execute(text("ALTER TABLE document_tasks ADD COLUMN user_id TEXT"))
