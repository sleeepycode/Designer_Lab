"""Проверки из backend_integration_changes.docx (§5–§13)."""

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
from app.main import create_app
from app.services import doc_service_client
from app.services.storage import list_project_uploaded_images, project_file_url, storage_relative_path


def _docx_bytes() -> bytes:
    doc = Document()
    doc.add_paragraph('x' * 320)
    stream = BytesIO()
    doc.save(stream)
    return stream.getvalue()


def _client(tmp_path):
    settings.storage_dir = str(tmp_path / 'storage')
    settings.projects_dir = str(tmp_path / 'storage' / 'projects')
    settings.input_dir = str(tmp_path / 'storage' / 'inputs')
    settings.output_dir = str(tmp_path / 'storage' / 'outputs')
    settings.report_dir = str(tmp_path / 'storage' / 'reports')
    settings.backend_public_url = 'http://127.0.0.1:8002'

    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
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

    test_app = create_app()
    test_app.dependency_overrides[get_db] = override_get_db
    return TestClient(test_app)


def test_storage_static_serves_user_image(tmp_path):
    with _client(tmp_path) as client:
        create = client.post(
            '/projects/upload',
            data={'user_id': 'u1'},
            files={
                'file': (
                    'lab.docx',
                    _docx_bytes(),
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                )
            },
        )
        project_id = create.json()['project_id']
        client.post(
            f'/projects/{project_id}/files',
            data={'user_id': 'u1'},
            files={'file': ('pic.png', b'\x89PNG', 'image/png')},
        )
        url = f'/storage/projects/{project_id}/images/pic.png'
        resp = client.get(url)
        assert resp.status_code == 200
        assert resp.content.startswith(b'\x89PNG')


def test_project_file_url_and_uploaded_images_contract(tmp_path):
    settings.backend_public_url = 'http://127.0.0.1:8002'
    settings.projects_dir = str(tmp_path / 'storage' / 'projects')
    pid = 'test-proj'
    images_dir = Path(settings.projects_dir) / pid / 'images'
    images_dir.mkdir(parents=True)
    img = images_dir / 'graph.png'
    img.write_bytes(b'png')

    rel = storage_relative_path(img)
    assert rel == f'storage/projects/{pid}/images/graph.png'
    assert project_file_url(img) == f'http://127.0.0.1:8002/{rel}'

    entries = list_project_uploaded_images(pid)
    assert len(entries) == 1
    assert entries[0]['source'] == 'user_uploaded_image'
    assert entries[0]['path'].startswith('http://127.0.0.1:8002/storage/')
    assert entries[0]['local_path'] == rel


def test_process_passes_uploaded_images_to_doc_service(tmp_path, monkeypatch):
    from app.services import orchestrator

    captured: dict = {}

    def track_pipeline(
        docx_path,
        project_id,
        title_page,
        topic,
        output_docx_path,
        uploaded_images=None,
    ):
        captured['uploaded_images'] = uploaded_images
        captured['title_page'] = title_page
        return {
            'extract': {'project_id': project_id},
            'apply_result': {'status': 'completed'},
            'project_id': project_id,
            'uploaded_images_count': len(uploaded_images or []),
        }

    monkeypatch.setattr(orchestrator, 'run_doc_service_pipeline', track_pipeline)

    with _client(tmp_path) as client:
        up = client.post(
            '/projects/upload',
            data={'user_id': 'u1'},
            files={
                'file': (
                    'lab.docx',
                    _docx_bytes(),
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                )
            },
        )
        pid = up.json()['project_id']
        client.post(
            f'/projects/{pid}/files',
            data={'user_id': 'u1'},
            files={'file': ('extra.jpg', b'jpg', 'image/jpeg')},
        )
        proc = client.post(
            f'/projects/{pid}/process',
            data={
                'user_id': 'u1',
                'faculty': 'ФКН',
                'department': 'ИПП',
                'student_group': 'БПИ2404',
                'lab_title': 'ЛР1',
                'lab_number': '1',
                'student_name': 'Иванов',
                'reviewer_name': 'Петров',
                'discipline': 'Алгоритмы',
            },
        )
        assert proc.status_code == 200
        assert len(captured.get('uploaded_images') or []) == 1
        assert captured['uploaded_images'][0]['filename'] == 'extra.jpg'
        assert captured['title_page']['faculty'] == 'ФКН'
