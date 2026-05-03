"""
Подсказки по изображениям проекта (таск 4).

Реализация: app.services.image_suggestions_engine — анализ файлов в images/,
OCR через Tesseract (при установленных зависимостях), эвристики типа и ключевых слов.

gost_module (другой сервис) — анализ DOCX по ГОСТ, не картинки.
"""

from __future__ import annotations

from app.services.image_suggestions_engine import build_image_suggestions_for_project

# обратная совместимость импортов
build_mock_suggestions_for_project = build_image_suggestions_for_project

__all__ = ["build_image_suggestions_for_project", "build_mock_suggestions_for_project"]
