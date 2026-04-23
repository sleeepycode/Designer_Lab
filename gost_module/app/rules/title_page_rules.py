from __future__ import annotations

from uuid import uuid4
from app.rules.base import BaseRule

TITLE_MARKERS = [
    'министерство',
    'университет',
    'институт',
    'кафедра',
    'факультет',
    'дисциплина',
    'лабораторная',
    'отчет',
    'отчёт',
    'выполнил',
    'выполнила',
    'проверил',
    'проверила',
    'студент',
    'группа'
]

IMPORTANT_MARKERS = [
    'лабораторная',
    'выполнил',
    'выполнила',
    'проверил',
    'проверила'
]


class TitlePageExistsRule(BaseRule):
    rule_id = 'title_page.exists'
    title = 'Проверка наличия титульного листа'
    severity = 'error'

    def check(self, document_model):
        issues = []
        fixes = []

        first_paragraphs = document_model.paragraphs[:25]
        full_text = '\n'.join(p.text.lower() for p in first_paragraphs if p.text)

        found_markers = [m for m in TITLE_MARKERS if m in full_text]
        found_important = [m for m in IMPORTANT_MARKERS if m in full_text]

        if len(found_markers) < 3 or len(found_important) < 1:
            issues.append({
                'issue_id': uuid4().hex,
                'rule_id': self.rule_id,
                'severity': self.severity,
                'message': 'Не найден титульный лист',
                'explanation': 'В начале документа найдено недостаточно признаков титульного листа.',
                'preview': 'Первые абзацы документа',
                'actual': f"markers_found={found_markers}",
                'expected': 'title_page_present',
                'can_auto_apply': False,
                'fix_id': None,
            })

        return issues, fixes


class TitlePageContentRule(BaseRule):
    rule_id = 'title_page.content'
    title = 'Проверка содержания титульного листа'

    def check(self, document_model):
        issues = []
        fixes = []

        title_paragraphs = [p for p in document_model.paragraphs[:25] if p.block_type == 'title_page']
        if not title_paragraphs:
            return issues, fixes

        title_text = '\n'.join(p.text.lower() for p in title_paragraphs)

        expected_groups = {
            'organization': ['университет', 'институт', 'колледж'],
            'department': ['кафедра', 'факультет'],
            'work_type': ['лабораторная', 'отчет', 'отчёт'],
            'author': ['выполнил', 'выполнила', 'студент', 'группа'],
            'reviewer': ['проверил', 'проверила', 'преподаватель']
        }

        missing_groups = []
        for group, variants in expected_groups.items():
            if not any(v in title_text for v in variants):
                missing_groups.append(group)

        if missing_groups:
            issues.append({
                'issue_id': uuid4().hex,
                'rule_id': self.rule_id,
                'severity': 'warning',
                'message': 'Титульный лист заполнен не полностью',
                'explanation': f"Не найдены группы элементов: {', '.join(missing_groups)}.",
                'preview': 'Титульный лист',
                'actual': 'missing_groups',
                'expected': 'all_basic_groups_present',
                'can_auto_apply': False,
                'fix_id': None,
            })

        return issues, fixes