"""
Проксирование изображений в ML и сохранение подсказок в metadata проекта.
"""

from __future__ import annotations

from pathlib import Path

from app.services import ml_client
from app.services.image_suggestions_engine import (
    pending_suggestion,
    suggestion_from_ml_item,
    upsert_image_suggestion,
)


def topic_from_metadata(metadata_block: dict) -> str:
    topic = (metadata_block.get("topic") or "").strip()
    return topic or "лабораторной работы"


def register_uploaded_image_in_metadata(
    metadata_block: dict,
    project_id: str,
    image_path: Path,
) -> dict:
    """После сохранения файла: вызов ML (если настроен) и upsert подсказки."""
    topic = topic_from_metadata(metadata_block)
    ml_results = metadata_block.setdefault("image_ml_results", {})

    if not ml_client.is_configured():
        suggestion = pending_suggestion(
            project_id,
            image_path,
            message="ML-сервис не настроен (ml_service_base_url в .env).",
        )
        upsert_image_suggestion(metadata_block, suggestion)
        return suggestion

    try:
        ml_item = ml_client.analyze_image_file(image_path, topic)
        ml_results[image_path.name] = ml_item
        suggestion = suggestion_from_ml_item(project_id, image_path, ml_item)
    except Exception as exc:
        ml_results[image_path.name] = {"error": str(exc), "path": str(image_path)}
        suggestion = pending_suggestion(project_id, image_path, message=str(exc))
        errors = metadata_block.setdefault("errors", [])
        errors.append(f"ML по изображению {image_path.name}: {exc}")

    upsert_image_suggestion(metadata_block, suggestion)
    return suggestion
