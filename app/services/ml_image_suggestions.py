"""
Подсказки по картинкам проекта.

OCR и смысловой разбор изображений — зона ML, не Backend №1.
"""

from app.services.image_suggestions_engine import build_image_suggestions_for_project

__all__ = ["build_image_suggestions_for_project"]
