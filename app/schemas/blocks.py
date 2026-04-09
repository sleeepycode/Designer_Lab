from dataclasses import dataclass, field
from typing import Literal, Any


BlockType = Literal["paragraph", "table", "image"]


@dataclass
class ParagraphBlock:
    type: Literal["paragraph"] = "paragraph"
    text: str = ""
    style_name: str | None = None
    is_empty: bool = False


@dataclass
class TableBlock:
    type: Literal["table"] = "table"
    rows: list[list[str]] = field(default_factory=list)
    caption: str | None = None


@dataclass
class ImageBlock:
    type: Literal["image"] = "image"
    image_path: str = ""
    width_px: int | None = None
    height_px: int | None = None
    caption: str | None = None