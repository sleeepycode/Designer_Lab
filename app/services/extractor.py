from __future__ import annotations

import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

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


def paragraph_contains_drawing(paragraph: Paragraph) -> bool:
    """
    Проверка, содержит ли абзац встроенное изображение.
    """
    xml = paragraph._p.xml
    return "<w:drawing" in xml or "<pic:pic" in xml


def extract_table_data(table: Table) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.rows:
        row_data = []
        for cell in row.cells:
            row_data.append(cell.text.strip())
        rows.append(row_data)
    return rows


def extract_blocks(docx_path: str, temp_media_dir: str) -> list:
    """
    Извлекает блоки документа в порядке следования.
    Изображения пока вытягиваются отдельно, а потом подставляются
    по порядку появления в абзацах с drawing.
    """
    doc = Document(docx_path)
    image_files = extract_images_from_docx(docx_path, temp_media_dir)
    image_index = 0

    blocks: list = []

    for item in iter_block_items(doc):
        if isinstance(item, Paragraph):
            text = item.text.strip()

            if paragraph_contains_drawing(item):
                image_path = image_files[image_index] if image_index < len(image_files) else ""
                blocks.append(
                    ImageBlock(
                        image_path=image_path,
                        caption=None,
                    )
                )
                image_index += 1

                if text:
                    blocks.append(
                        ParagraphBlock(
                            text=text,
                            style_name=item.style.name if item.style else None,
                            is_empty=False,
                        )
                    )
            else:
                blocks.append(
                    ParagraphBlock(
                        text=text,
                        style_name=item.style.name if item.style else None,
                        is_empty=(text == ""),
                    )
                )

        elif isinstance(item, Table):
            blocks.append(
                TableBlock(
                    rows=extract_table_data(item),
                    caption=None,
                )
            )

    return blocks