import json
from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.db import Base, get_db
from app.main import app


def _docx_bytes() -> bytes:
    doc = Document()
    doc.add_paragraph("test")
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def _client(tmp_path):
    settings.storage_dir = str(tmp_path / "storage")
    settings.input_dir = str(tmp_path / "storage" / "inputs")
    settings.output_dir = str(tmp_path / "storage" / "outputs")
    settings.report_dir = str(tmp_path / "storage" / "reports")
    settings.projects_dir = str(tmp_path / "storage" / "projects")

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_upload_project_file_creates_project_structure(tmp_path):
    with _client(tmp_path) as client:
        files = {
            "file": (
                "source.docx",
                _docx_bytes(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        resp = client.post("/projects/upload", data={"user_id": "user-1"}, files=files)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "uploaded"
        project_id = body["project_id"]

        project_dir = Path(settings.projects_dir) / project_id
        assert (project_dir / "input").exists()
        assert (project_dir / "images").exists()
        assert (project_dir / "output").exists()
        metadata_path = project_dir / "metadata.json"
        assert metadata_path.exists()

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert metadata["project_id"] == project_id
        assert metadata["status"] == "uploaded"


def test_upload_project_file_rejects_unsupported_extension(tmp_path):
    with _client(tmp_path) as client:
        files = {"file": ("notes.txt", b"text", "text/plain")}
        resp = client.post("/projects/upload", files=files)
        assert resp.status_code == 400
        assert "Поддерживаются только форматы" in resp.json()["message"]
