from app.schemas.blocks import ParagraphBlock


TITLE_KEYWORDS = [
    "министерство",
    "университет",
    "институт",
    "кафедра",
    "факультет",
    "лабораторная работа",
    "выполнил",
    "проверил",
    "руководитель",
    "москва",
]

BODY_START_KEYWORDS = [
    "введение",
    "цель работы",
    "цель лабораторной работы",
    "ход работы",
    "теоретические сведения",
    "практическая часть",
    "выполнение работы",
    "заключение",
]


def normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def is_title_like(text: str) -> bool:
    t = normalize_text(text)
    return any(keyword in t for keyword in TITLE_KEYWORDS)


def is_body_start(text: str) -> bool:
    t = normalize_text(text)
    return any(t.startswith(keyword) for keyword in BODY_START_KEYWORDS)


def _find_body_start_index(blocks: list) -> int | None:
    for i, block in enumerate(blocks[:40]):
        if isinstance(block, ParagraphBlock):
            text = block.text.strip()
            if not text:
                continue

            if is_body_start(text):
                return i
    return None


def _find_first_non_title_index(blocks: list, start: int = 0) -> int | None:
    for i, block in enumerate(blocks[start:], start=start):
        if isinstance(block, ParagraphBlock):
            text = block.text.strip()
            if not text:
                continue
            if not is_title_like(text):
                return i
    return None


def remove_existing_title_page(blocks: list) -> list:
    """Удаляет старый титульник из начала документа."""
    title_like_count = 0
    has_title_page_keywords = False

    for i, block in enumerate(blocks[:40]):
        if isinstance(block, ParagraphBlock):
            text = block.text.strip()
            if not text:
                continue

            if is_title_like(text):
                title_like_count += 1

            normalized = normalize_text(text)
            if normalized.startswith("выполнил") or normalized.startswith("проверил"):
                has_title_page_keywords = True

    body_start_index = _find_body_start_index(blocks)
    if body_start_index is not None:
        return blocks[body_start_index:]

    if title_like_count >= 3 or has_title_page_keywords:
        first_non_title = _find_first_non_title_index(blocks)
        if first_non_title is not None:
            return blocks[first_non_title:]

    return blocks