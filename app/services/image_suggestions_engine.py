"""
Подсказки по изображениям: только формат ответа ML для фронта.

Backend №1 не делает OCR и не угадывает тип рисунка по имени файла.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from app.core.config import settings


def stable_suggestion_id(project_id: str, image_path: Path) -> str:
    raw = f"{project_id}|{image_path.resolve()}".encode("utf-8", errors="replace")
    return f"img-{hashlib.sha256(raw).hexdigest()[:16]}"


def upsert_image_suggestion(metadata_block: dict, suggestion: dict) -> None:
    suggestions = metadata_block.get("image_suggestions") or []
    sid = suggestion.get("id")
    if sid:
        suggestions = [s for s in suggestions if s.get("id") != sid]
    suggestions.append(suggestion)
    metadata_block["image_suggestions"] = suggestions


def suggestion_from_ml_item(project_id: str, img_path: Path, ml_item: dict) -> dict:
    placement = ml_item.get("placement") or {}
    reason = (placement.get("reason") or "").strip()
    if not reason:
        reason = "Место вставки уточняется после анализа документа."

    error = ml_item.get("error")
    ocr_text = ml_item.get("ocr_text") or ""

    return {
        "id": stable_suggestion_id(project_id, img_path),
        "image_path": str(img_path),
        "image_name": img_path.name,
        "image_type": ml_item.get("type") or "unknown",
        "ocr_text": ocr_text,
        "ocr_status": "error" if error else "ok",
        "ocr_error": error,
        "keywords": ml_item.get("keywords") or [],
        "suggested_insertion": reason,
        "caption": ml_item.get("caption") or f"Рисунок — {img_path.stem.replace('_', ' ')}",
        "confidence": ml_item.get("confidence"),
        "applied": False,
    }


def pending_suggestion(project_id: str, img_path: Path, *, message: str) -> dict:
    return {
        "id": stable_suggestion_id(project_id, img_path),
        "image_path": str(img_path),
        "image_name": img_path.name,
        "image_type": "unknown",
        "ocr_text": "",
        "ocr_status": "pending",
        "ocr_error": message,
        "keywords": [],
        "suggested_insertion": "",
        "caption": img_path.stem.replace("_", " "),
        "applied": False,
    }


def list_project_image_paths(project_id: str) -> list[Path]:
    images_dir = Path(settings.projects_dir) / project_id / "images"
    if not images_dir.is_dir():
        return []
    return sorted(
        [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}],
        key=lambda p: p.name.lower(),
    )


def build_image_suggestions_from_metadata(project_id: str, metadata_block: dict) -> list[dict]:
    """Собрать подсказки из ML-результатов; для файлов без ответа — заглушка pending."""
    stored = {s.get("image_name"): s for s in (metadata_block.get("image_suggestions") or []) if s.get("image_name")}
    ml_results = metadata_block.get("image_ml_results") or {}
    out: list[dict] = []

    for img_path in list_project_image_paths(project_id):
        if img_path.name in stored:
            out.append(stored[img_path.name])
            continue
        ml_item = ml_results.get(img_path.name)
        if isinstance(ml_item, dict) and not ml_item.get("error"):
            out.append(suggestion_from_ml_item(project_id, img_path, ml_item))
        else:
            err = (ml_item or {}).get("error") if isinstance(ml_item, dict) else None
            out.append(
                pending_suggestion(
                    project_id,
                    img_path,
                    message=err or "Ожидается ответ ML после загрузки изображения.",
                )
            )
    return out
