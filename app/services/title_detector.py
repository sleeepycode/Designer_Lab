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


def remove_existing_title_page(blocks: list) -> list:
    """
    Удаляет старый титульник по эвристике.
    """
    title_like_count = 0
    body_start_index = None

    for i, block in enumerate(blocks[:25]):
        if isinstance(block, ParagraphBlock):
            text = block.text.strip()
            if not text:
                continue

            if is_title_like(text):
                title_like_count += 1

            if is_body_start(text):
                body_start_index = i
                break

    if title_like_count >= 2 and body_start_index is not None:
        return blocks[body_start_index:]

    return blocks