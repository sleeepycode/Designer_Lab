from __future__ import annotations

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

from app.core.config import settings
from app.services.docx_extractor import iter_block_items


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
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not text:
                continue

            if is_body_start(text):
                return i
    return None


def remove_existing_title_page(doc: Document) -> None:
    """
    Удаляет существующий титульный лист из документа, если он найден.
    """
    blocks = list(iter_block_items(doc))
    body_start_index = _find_body_start_index(blocks)
    if body_start_index is not None and body_start_index > 0:
        # Удалить блоки от 0 до body_start_index - 1
        body = doc.element.body
        children = list(body)
        for i in range(body_start_index):
            body.remove(children[i])


def generate_title_page(
    input_path: str,
    output_path: str,
    department: str,
    discipline: str,
    lab_number: str,
    topic: str,
    full_name: str,
    group: str,
    teacher: str
) -> None:
    """
    Добавляет титульный лист в начало существующего .docx документа.
    Если титульный лист уже существует, заменяет его на новый.

    :param input_path: Путь к входному .docx файлу
    :param output_path: Путь к выходному .docx файлу
    :param department: Кафедра
    :param discipline: Дисциплина
    :param lab_number: Номер лабораторной работы
    :param topic: Тема
    :param full_name: ФИО
    :param group: Группа
    :param teacher: Преподаватель
    """
    doc = Document(input_path)

    # Удалить существующий титульный лист, если есть
    remove_existing_title_page(doc)

    # Вставляем титульный лист в начало документа
    # Сначала добавляем разрыв страницы в конце титульного листа, чтобы отделить от остального документа

    # Университет
    p = doc.paragraphs[0] if doc.paragraphs else doc.add_paragraph()
    p.insert_paragraph_before(settings.university_name)
    p = doc.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(12)

    # Пустая строка
    doc.paragraphs[0].insert_paragraph_before('')

    # Кафедра
    p = doc.paragraphs[0].insert_paragraph_before(f"Кафедра: {department}")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)

    # Дисциплина
    p = doc.paragraphs[0].insert_paragraph_before(f"Дисциплина: {discipline}")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)

    # Номер лабораторной работы
    p = doc.paragraphs[0].insert_paragraph_before(f"Лабораторная работа № {lab_number}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)
        run.bold = True

    # Тема
    p = doc.paragraphs[0].insert_paragraph_before(f"Тема: {topic}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)

    # Пустая строка
    doc.paragraphs[0].insert_paragraph_before('')

    # Выполнил
    p = doc.paragraphs[0].insert_paragraph_before(f"Выполнил: {full_name}")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)

    # Группа
    p = doc.paragraphs[0].insert_paragraph_before(f"Группа: {group}")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)

    # Преподаватель
    p = doc.paragraphs[0].insert_paragraph_before(f"Преподаватель: {teacher}")
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)

    # Пустая строка
    doc.paragraphs[0].insert_paragraph_before('')

    # Город и год
    p = doc.paragraphs[0].insert_paragraph_before(f"{settings.city} {settings.year}")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in p.runs:
        run.font.name = settings.font_name
        run.font.size = Pt(settings.font_size_pt)

    # Добавляем разрыв страницы после титульного листа
    run = doc.paragraphs[-1].add_run()
    run.add_break(WD_BREAK.PAGE)

    # Сохранение документа
    doc.save(output_path)