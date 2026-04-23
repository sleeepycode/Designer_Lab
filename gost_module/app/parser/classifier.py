from __future__ import annotations

TITLE_KEYWORDS = [
    'министерство',
    'университет',
    'институт',
    'колледж',
    'кафедра',
    'факультет',
    'дисциплина',
    'лабораторная',
    'лабораторная работа',
    'отчет',
    'отчёт',
    'выполнил',
    'выполнила',
    'проверил',
    'проверила',
    'студент',
    'группа',
    'преподаватель'
]


def classify_paragraph(text: str, index: int, style_name: str | None, alignment: str | None) -> str:
    normalized = text.strip()
    low = normalized.lower()

    if not normalized:
        return 'empty'

    if index < 25:
        score = 0

        for word in TITLE_KEYWORDS:
            if word in low:
                score += 1

        if alignment and 'CENTER' in alignment.upper():
            score += 1

        if len(normalized) < 120:
            score += 1

        if score >= 2:
            return 'title_page'

    if style_name and 'heading' in style_name.lower():
        return 'heading'

    if len(normalized) <= 100 and normalized == normalized.upper() and any(ch.isalpha() for ch in normalized):
        return 'heading'

    if len(normalized) <= 100 and alignment and 'CENTER' in alignment.upper():
        if not normalized.endswith('.'):
            return 'heading'

    return 'body'