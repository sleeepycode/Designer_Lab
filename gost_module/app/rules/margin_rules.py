from __future__ import annotations

from uuid import uuid4

from app.rules.base import BaseRule

EXPECTED_LEFT_CM = 3.0
EXPECTED_RIGHT_CM = 1.5
EXPECTED_TOP_CM = 2.0
EXPECTED_BOTTOM_CM = 2.0


class MarginRule(BaseRule):
    rule_id = 'page.margins'
    title = 'Проверка полей страницы'

    def check(self, document_model):
        issues = []
        fixes = []
        for section in document_model.sections:
            expected_pairs = [
                ('left_margin_cm', EXPECTED_LEFT_CM, 'set_left_margin'),
                ('right_margin_cm', EXPECTED_RIGHT_CM, 'set_right_margin'),
                ('top_margin_cm', EXPECTED_TOP_CM, 'set_top_margin'),
                ('bottom_margin_cm', EXPECTED_BOTTOM_CM, 'set_bottom_margin'),
            ]
            for attr, expected, action in expected_pairs:
                actual = getattr(section, attr)
                if actual != expected:
                    fix_id = uuid4().hex
                    issues.append({
                        'issue_id': uuid4().hex,
                        'rule_id': self.rule_id,
                        'severity': self.severity,
                        'message': f'Неверное значение поля {attr}',
                        'explanation': 'Поля страницы должны соответствовать шаблону лабораторной работы.',
                        'preview': f'Секция {section.id}',
                        'actual': str(actual),
                        'expected': str(expected),
                        'can_auto_apply': True,
                        'fix_id': fix_id,
                    })
                    fixes.append({
                        'fix_id': fix_id,
                        'action': action,
                        'target_type': 'section',
                        'target_id': section.id,
                        'old_value': str(actual),
                        'new_value': str(expected),
                    })
        return issues, fixes
