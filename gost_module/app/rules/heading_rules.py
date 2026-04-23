from __future__ import annotations

from uuid import uuid4

from app.rules.base import BaseRule


class HeadingPeriodRule(BaseRule):
    rule_id = 'heading.no_period'
    title = 'Проверка точки в конце заголовка'

    def check(self, document_model):
        issues = []
        fixes = []
        for paragraph in document_model.paragraphs:
            if paragraph.block_type != 'heading':
                continue
            text = paragraph.text.strip()
            if text.endswith('.'):
                fix_id = uuid4().hex
                issues.append({
                    'issue_id': uuid4().hex,
                    'rule_id': self.rule_id,
                    'severity': self.severity,
                    'message': 'В конце заголовка не должно быть точки',
                    'explanation': 'Заголовки разделов оформляются без точки в конце.',
                    'paragraph_id': paragraph.id,
                    'preview': paragraph.text[:120],
                    'actual': text,
                    'expected': text.rstrip('.'),
                    'can_auto_apply': True,
                    'fix_id': fix_id,
                })
                fixes.append({
                    'fix_id': fix_id,
                    'action': 'remove_trailing_period',
                    'target_type': 'paragraph_text',
                    'target_id': paragraph.id,
                    'old_value': text,
                    'new_value': text.rstrip('.'),
                })
        return issues, fixes
