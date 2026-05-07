from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Iterator

from docx import Document
from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.schemas.blocks import ParagraphBlock, TableBlock, ImageBlock


def iter_block_items(parent: DocxDocument) -> Iterator[Paragraph | Table]:
    """
    Идёт по телу документа в реальном порядке элементов:
    paragraph -> table -> paragraph -> ...
    """
    body = parent.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def extract_images_from_docx(docx_path: str, media_dir: str) -> list[str]:
    """
    Извлекает все картинки из DOCX как zip-архива.
    Пока без точной привязки к абзацу; файлы сохраняются локально.
    """
    media_paths: list[str] = []
    media_root = Path(media_dir)
    media_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(docx_path, "r") as archive:
        for name in archive.namelist():
            if name.startswith("word/media/"):
                filename = Path(name).name
                target = media_root / filename
                with archive.open(name) as src, target.open("wb") as dst:
                    dst.write(src.read())
                media_paths.append(str(target))

    return media_paths


def extract_docx_content(docx_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Извлекает содержимое из .docx файла и приводит к единой структуре JSON.

    :param docx_path: Путь к .docx файлу
    :param output_dir: Директория для сохранения извлеченных изображений
    :return: Словарь с ключами 'paragraphs', 'tables', 'images'
    """
    doc = Document(docx_path)

    # Извлечение изображений
    images = extract_images_from_docx(docx_path, output_dir)

    paragraphs: List[str] = []
    tables: List[List[List[str]]] = []

    # Итерация по блокам документа
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:  # Игнорировать пустые абзацы
                paragraphs.append(text)
        elif isinstance(block, Table):
            table_data = []
            for row in block.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            tables.append(table_data)

    return {
        "paragraphs": paragraphs,
        "tables": tables,
        "images": images
    }


def extract_blocks(docx_path: str, media_dir: str) -> list:
    """
    Извлекает блоки из DOCX: параграфы, таблицы, изображения.
    """
    doc = Document(docx_path)
    media_paths = extract_images_from_docx(docx_path, media_dir)
    blocks = []

    image_index = 0
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if text:
                blocks.append(ParagraphBlock(text=text))
        elif isinstance(block, Table):
            table_data = []
            for row in block.rows:
                row_data = [cell.text.strip() for cell in row.cells]
                table_data.append(row_data)
            blocks.append(TableBlock(rows=table_data))
        # Для изображений: если есть media_paths, добавляем ImageBlock
        # Но привязка изображений к абзацам сложная, пока пропустим

    # Добавляем изображения как отдельные блоки, если есть
    for media_path in media_paths:
        blocks.append(ImageBlock(image_path=media_path))

    return blocks