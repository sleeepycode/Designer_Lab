import re

from app.schemas.blocks import ParagraphBlock, TableBlock, ImageBlock


FIGURE_RE = re.compile(r"^\s*рисунок\s+\d+", re.IGNORECASE)
TABLE_RE = re.compile(r"^\s*таблица\s+\d+", re.IGNORECASE)


def is_figure_caption(text: str) -> bool:
    return bool(FIGURE_RE.match(text.strip()))


def is_table_caption(text: str) -> bool:
    return bool(TABLE_RE.match(text.strip()))


def attach_captions(blocks: list) -> list:
    """
    Ищет подписи рядом с таблицами/рисунками и привязывает их к блокам.
    После привязки отдельный paragraph-caption можно удалить из потока.
    """
    result = []
    i = 0

    while i < len(blocks):
        block = blocks[i]

        if isinstance(block, TableBlock):
            if i > 0 and isinstance(blocks[i - 1], ParagraphBlock):
                prev_text = blocks[i - 1].text.strip()
                if is_table_caption(prev_text):
                    block.caption = prev_text
                    if result and result[-1] is blocks[i - 1]:
                        result.pop()

            if i + 1 < len(blocks) and isinstance(blocks[i + 1], ParagraphBlock):
                next_text = blocks[i + 1].text.strip()
                if is_table_caption(next_text):
                    block.caption = next_text
                    i += 1

            result.append(block)

        elif isinstance(block, ImageBlock):
            if i + 1 < len(blocks) and isinstance(blocks[i + 1], ParagraphBlock):
                next_text = blocks[i + 1].text.strip()
                if is_figure_caption(next_text):
                    block.caption = next_text
                    i += 1

            elif i > 0 and isinstance(blocks[i - 1], ParagraphBlock):
                prev_text = blocks[i - 1].text.strip()
                if is_figure_caption(prev_text):
                    block.caption = prev_text
                    if result and result[-1] is blocks[i - 1]:
                        result.pop()

            result.append(block)

        else:
            result.append(block)

        i += 1

    return result


def ensure_generated_captions(blocks: list) -> list:
    figure_num = 1
    table_num = 1

    for block in blocks:
        if isinstance(block, ImageBlock):
            if not block.caption:
                block.caption = f"Рисунок {figure_num}"
            figure_num += 1

        elif isinstance(block, TableBlock):
            if not block.caption:
                block.caption = f"Таблица {table_num}"
            table_num += 1

    return blocks