"""
Движок подсказок по изображениям проекта (таск 4).

Поля как в ТЗ: тип, OCR, ключевые слова, место вставки, подпись.
Без «выдуманного» OCR: текст берётся из Tesseract, если установлены Pillow + pytesseract + бинарник Tesseract.
Иначе ocr_text пустой, в поле ocr_status — понятная причина.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from app.core.config import settings

_SCHEMA_HINTS = ("схем", "schema", "diagram", "график", "chart", "plot", "рис", "fig", "figure")
_SCREEN_HINTS = ("screen", "скрин", "screenshot", "clip")


def _stable_suggestion_id(project_id: str, image_path: Path) -> str:
    raw = f"{project_id}|{image_path.resolve()}".encode("utf-8", errors="replace")
    return f"img-{hashlib.sha256(raw).hexdigest()[:16]}"


def _infer_image_type(img_path: Path, width: int | None, height: int | None) -> str:
    stem = img_path.stem.lower()
    for h in _SCHEMA_HINTS:
        if h in stem:
            return "schema"
    for h in _SCREEN_HINTS:
        if h in stem:
            return "screenshot"
    if width and height and height > 0:
        ratio = width / height
        if ratio > 1.6 or ratio < 0.63:
            return "diagram"
    return "photo"


def _keywords_from_filename_and_ocr(stem: str, ocr_text: str, limit: int = 12) -> list[str]:
    parts = re.split(r"[\s_\-–—.]+", stem)
    kws = [p for p in parts if len(p) > 1]
    if ocr_text:
        words = re.findall(r"[А-Яа-яA-Za-z]{3,}", ocr_text)
        kws.extend(words[:20])
    seen: set[str] = set()
    out: list[str] = []
    for w in kws:
        lw = w.lower()
        if lw in seen:
            continue
        seen.add(lw)
        out.append(w if any("\u0400" <= c <= "\u04FF" for c in w) else w.lower())
        if len(out) >= limit:
            break
    return out if out else ["изображение"]


def _run_ocr_on_image(im) -> tuple[str, str | None]:
    try:
        import pytesseract
    except ImportError:
        return "", "Установите pytesseract (pip install pytesseract) и Tesseract OCR в системе."

    try:
        rgb = im.convert("RGB")
        text = pytesseract.image_to_string(rgb, lang="rus+eng")
        return (text.strip(), None)
    except Exception as exc:
        return "", str(exc)


def build_image_suggestions_for_project(project_id: str) -> list[dict]:
    images_dir = Path(settings.projects_dir) / project_id / "images"
    if not images_dir.is_dir():
        return []

    paths = sorted(
        [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}],
        key=lambda p: p.name.lower(),
    )
    suggestions: list[dict] = []

    try:
        from PIL import Image as PILImage
    except ImportError:
        PILImage = None  # type: ignore[misc, assignment]

    for idx, img_path in enumerate(paths, start=1):
        width = height = None
        ocr_text = ""
        ocr_err: str | None = "Установите pillow (pip install pillow) для анализа изображений."
        if PILImage is not None:
            try:
                with PILImage.open(img_path) as im:
                    width, height = im.size
                    ocr_text, ocr_err = _run_ocr_on_image(im)
            except Exception as exc:
                ocr_err = str(exc)

        image_type = _infer_image_type(img_path, width, height)
        ocr_status = "ok" if ocr_text else ("error" if ocr_err else "empty")

        keywords = _keywords_from_filename_and_ocr(img_path.stem, ocr_text)
        caption = f"Рисунок {idx} — {img_path.stem.replace('_', ' ')}"

        item = {
            "id": _stable_suggestion_id(project_id, img_path),
            "image_path": str(img_path),
            "image_name": img_path.name,
            "image_type": image_type,
            "ocr_text": ocr_text,
            "ocr_status": ocr_status,
            "keywords": keywords,
            "suggested_insertion": "после раздела «Ход работы», перед разделом «Выводы»",
            "caption": caption,
            "applied": False,
        }
        if ocr_err:
            item["ocr_error"] = ocr_err
        suggestions.append(item)
    return suggestions
