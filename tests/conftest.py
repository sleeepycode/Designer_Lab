from io import BytesIO
from pathlib import Path

import pytest
from docx import Document

from app.services import doc_service_client, ml_client, orchestrator


def _minimal_docx_bytes() -> bytes:
    doc = Document()
    doc.add_paragraph('x' * 320)
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


@pytest.fixture(autouse=True)
def mock_external_services(monkeypatch, tmp_path):
    def fake_extract(docx_path: Path, project_id: str | None = None) -> dict:
        return {
            'paragraphs': [{'id': 'paragraph_1', 'text': 't' * 320, 'type': 'paragraph'}],
            'tables': [],
            'images': [],
            'project_id': project_id,
        }

    def fake_apply(
        project_id: str,
        title_page: dict,
        topic: str,
        ml_response=None,
        uploaded_images=None,
        **_kwargs,
    ) -> dict:
        return {
            'status': 'completed',
            'project_id': project_id,
            'topic': topic,
            'uploaded_images_count': len(uploaded_images or []),
        }

    def fake_info(project_id: str) -> dict:
        return {'project_id': project_id, 'has_extracted_data': True, 'files': []}

    def fake_download_docx(project_id: str, dest_path: str | Path) -> Path:
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(_minimal_docx_bytes())
        return dest

    monkeypatch.setattr(doc_service_client, 'extract_document', fake_extract)
    monkeypatch.setattr(doc_service_client, 'apply_ml_changes', fake_apply)
    monkeypatch.setattr(doc_service_client, 'get_project_info', fake_info)
    monkeypatch.setattr(doc_service_client, 'download_docx', fake_download_docx)
    monkeypatch.setattr(orchestrator, 'extract_via_doc_service', fake_extract)

    def fake_pipeline(
        docx_path,
        project_id,
        title_page,
        topic,
        output_docx_path,
        uploaded_images=None,
    ):
        fake_extract(docx_path, project_id)
        result = fake_apply(
            project_id,
            title_page,
            topic,
            ml_response={'generated_sections': [], 'bibliography': []},
            uploaded_images=uploaded_images,
        )
        fake_download_docx(project_id, output_docx_path)
        return {
            'extract': fake_extract(docx_path, project_id),
            'apply_result': result,
            'project_id': project_id,
            'uploaded_images_count': len(uploaded_images or []),
        }

    monkeypatch.setattr(orchestrator, 'run_doc_service_pipeline', fake_pipeline)
    monkeypatch.setattr(doc_service_client, 'ping', lambda: {'ok': True})

    def fake_analyze_image_file(image_path, topic, document_text='', project_id=None):
        return {
            'path': str(image_path),
            'type': 'diagram',
            'ocr_text': 'U=IR',
            'keywords': ['график', 'напряжение'],
            'caption': 'Рисунок 1 — График зависимости',
            'placement': {
                'paragraph_index': 3,
                'score': 0.82,
                'reason': 'после абзаца с описанием эксперимента',
            },
            'confidence': 0.82,
            'error': None,
        }

    monkeypatch.setattr(ml_client, 'is_configured', lambda: True)
    monkeypatch.setattr(ml_client, 'analyze_image_file', fake_analyze_image_file)
