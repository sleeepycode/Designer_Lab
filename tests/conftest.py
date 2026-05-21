from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from app.services import doc_service_client, ml_client, orchestrator


def _minimal_docx_bytes() -> bytes:
    doc = Document()
    doc.add_paragraph("x" * 320)
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch, tmp_path):
    def fake_extract(docx_path: Path, project_id: str | None = None) -> dict:
        return {
            "paragraphs": [{"id": "paragraph_1", "text": "t" * 320, "type": "paragraph"}],
            "tables": [],
            "images": [],
        }

    def fake_ml(document_text: str, image_paths: list[str], topic: str) -> dict:
        return {
            "success": True,
            "summary": {"topic": topic},
            "report": {"generated_sections": [], "bibliography": []},
            "images": [],
            "content_suggestions": [],
            "errors": [],
            "meta": {},
        }

    def fake_apply(project_id: str, ml_response: dict, title_page: dict) -> None:
        return None

    def fake_download(project_id: str, dest_path: str | Path) -> Path:
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(_minimal_docx_bytes())
        return dest

    monkeypatch.setattr(doc_service_client, "extract_document", fake_extract)
    monkeypatch.setattr(doc_service_client, "apply_ml_changes", fake_apply)
    monkeypatch.setattr(doc_service_client, "download_result", fake_download)
    monkeypatch.setattr(ml_client, "analyze_document", fake_ml)
    monkeypatch.setattr(orchestrator, "extract_via_doc_service", fake_extract)
    monkeypatch.setattr(orchestrator, "run_ml_analysis", fake_ml)
    monkeypatch.setattr(
        orchestrator,
        "build_doc_service_result",
        lambda project_id, ml_response, title_page, output_path: fake_download(project_id, output_path),
    )
    monkeypatch.setattr(doc_service_client, "ping", lambda: {"ok": True})
    monkeypatch.setattr(ml_client, "ping", lambda: {"ok": True})
