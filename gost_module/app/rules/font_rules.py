from __future__ import annotations

from uuid import uuid4

from app.rules.base import BaseRule

EXPECTED_FONT_NAME = 'Times New Roman'
EXPECTED_FONT_SIZE = 14.0


class FontNameRule(BaseRule):
    rule_id = 'body.font.name'
    title = 'Проверка названия шрифта'

    def check(self, document_model):
        issues = []
        fixes = []

        for paragraph in document_model.paragraphs:
            if paragraph.block_type != 'body':
                continue

            for run in paragraph.runs:
                if not run.text.strip():
                    continue
                if run.font_name and run.font_name != EXPECTED_FONT_NAME:
                    fix_id = uuid4().hex
                    issues.append({
                        'issue_id': uuid4().hex,
                        'rule_id': self.rule_id,
                        'severity': self.severity,
                        'message': 'Неверный шрифт',
                        'explanation': 'Для основного текста должен использоваться Times New Roman.',
                        'paragraph_id': paragraph.id,
                        'run_id': run.id,
                        'preview': paragraph.text[:120],
                        'actual': str(run.font_name),
                        'expected': EXPECTED_FONT_NAME,
                        'can_auto_apply': True,
                        'fix_id': fix_id,
                    })
                    fixes.append({
                        'fix_id': fix_id,
                        'action': 'set_font_name',
                        'target_type': 'run',
                        'target_id': run.id,
                        'old_value': str(run.font_name),
                        'new_value': EXPECTED_FONT_NAME,
                    })

        return issues, fixes


class FontSizeRule(BaseRule):
    rule_id = 'body.font.size'
    title = 'Проверка размера шрифта'

    def check(self, document_model):
        issues = []
        fixes = []

        for paragraph in document_model.paragraphs:
            if paragraph.block_type != 'body':
                continue

            for run in paragraph.runs:
                if not run.text.strip():
                    continue
                if run.font_size_pt not in (None, EXPECTED_FONT_SIZE):
                    fix_id = uuid4().hex
                    issues.append({
                        'issue_id': uuid4().hex,
                        'rule_id': self.rule_id,
                        'severity': self.severity,
                        'message': 'Неверный размер шрифта',
                        'explanation': 'Для основного текста должен использоваться размер 14 pt.',
                        'paragraph_id': paragraph.id,
                        'run_id': run.id,
                        'preview': paragraph.text[:120],
                        'actual': str(run.font_size_pt),
                        'expected': str(EXPECTED_FONT_SIZE),
                        'can_auto_apply': True,
                        'fix_id': fix_id,
                    })
                    fixes.append({
                        'fix_id': fix_id,
                        'action': 'set_font_size',
                        'target_type': 'run',
                        'target_id': run.id,
                        'old_value': str(run.font_size_pt),
                        'new_value': str(EXPECTED_FONT_SIZE),
                    })

        return issues, fixes
