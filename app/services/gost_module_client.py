"""
HTTP-клиент к отдельному сервису gost_module (ветка ML репозитория).

Запуск второго приложения, например:
  cd Designer_Lab_ML/gost_module && uvicorn app.main:app --reload --port 9001

В .env основного бэка:
  gost_module_base_url=http://127.0.0.1:9001
"""

from __future__ import annotations

from pathlib import Path

import httpx

from app.core.config import settings


def call_gost_module_analyze(docx_path: Path) -> dict | None:
    """
    POST /analyze с multipart file — как в README gost_module.
    Если gost_module_base_url не задан, возвращает None (интеграция выключена).
    """
    base = (settings.gost_module_base_url or "").strip().rstrip("/")
    if not base:
        return None
    if not docx_path.is_file():
        return None

    url = f"{base}/analyze"
    with docx_path.open("rb") as f:
        files = {
            "file": (
                docx_path.name,
                f,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(url, files=files)
    response.raise_for_status()
    return response.json()
