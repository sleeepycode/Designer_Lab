<<<<<<< HEAD
from sqlalchemy import create_engine
=======
from sqlalchemy import create_engine, text
>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
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
<<<<<<< HEAD
=======


def ensure_schema_compatibility() -> None:
    """Apply minimal non-destructive SQLite schema updates for local MVP."""
    with engine.begin() as conn:
        result = conn.execute(text("PRAGMA table_info(document_tasks)"))
        columns = {row[1] for row in result}
        
        # Добавить отсутствующие колонки
        if "callback_url" not in columns:
            conn.execute(text("ALTER TABLE document_tasks ADD COLUMN callback_url TEXT"))
        if "celery_task_id" not in columns:
            conn.execute(text("ALTER TABLE document_tasks ADD COLUMN celery_task_id TEXT"))
        if "result" not in columns:
            conn.execute(text("ALTER TABLE document_tasks ADD COLUMN result JSON"))
        if "updated_at" not in columns:
            conn.execute(text("ALTER TABLE document_tasks ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))

>>>>>>> 497a3e5 (Обработка файла, применение титульного листа, по данным из формы в JSON формате. Валидация входного документа, сохранение ошибок и предупреждений в БД, если таковые имеются.)
