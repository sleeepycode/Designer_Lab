from __future__ import annotations

from uuid import uuid4

from app.rules.base import BaseRule

EXPECTED_FIRST_LINE_INDENT_CM = 1.25
EXPECTED_LINE_SPACING = 1.5
EXPECTED_SPACE_BEFORE_PT = 0.0
EXPECTED_SPACE_AFTER_PT = 0.0
EXPECTED_ALIGNMENT = 'JUSTIFY'


def _alignment_ok(alignment: str | None) -> bool:
    if alignment is None:
        return False
    return EXPECTED_ALIGNMENT in alignment.upper()


class FirstLineIndentRule(BaseRule):
    rule_id = 'body.first_line_indent'
    title = 'Проверка абзацного отступа'

    def check(self, document_model):
        issues = []
        fixes = []
        for paragraph in document_model.paragraphs:
            if paragraph.block_type != 'body' or not paragraph.text.strip():
                continue
            if paragraph.first_line_indent_cm != EXPECTED_FIRST_LINE_INDENT_CM:
                fix_id = uuid4().hex
                issues.append({
                    'issue_id': uuid4().hex,
                    'rule_id': self.rule_id,
                    'severity': self.severity,
                    'message': 'Неверный абзацный отступ',
                    'explanation': 'Отступ первой строки основного текста должен быть 1.25 см.',
                    'paragraph_id': paragraph.id,
                    'preview': paragraph.text[:120],
                    'actual': str(paragraph.first_line_indent_cm),
                    'expected': str(EXPECTED_FIRST_LINE_INDENT_CM),
                    'can_auto_apply': True,
                    'fix_id': fix_id,
                })
                fixes.append({
                    'fix_id': fix_id,
                    'action': 'set_first_line_indent',
                    'target_type': 'paragraph',
                    'target_id': paragraph.id,
                    'old_value': str(paragraph.first_line_indent_cm),
                    'new_value': str(EXPECTED_FIRST_LINE_INDENT_CM),
                })
        return issues, fixes


class LineSpacingRule(BaseRule):
    rule_id = 'body.line_spacing'
    title = 'Проверка межстрочного интервала'

    def check(self, document_model):
        issues = []
        fixes = []
        for paragraph in document_model.paragraphs:
            if paragraph.block_type != 'body' or not paragraph.text.strip():
                continue
            if paragraph.line_spacing != EXPECTED_LINE_SPACING:
                fix_id = uuid4().hex
                issues.append({
                    'issue_id': uuid4().hex,
                    'rule_id': self.rule_id,
                    'severity': self.severity,
                    'message': 'Неверный межстрочный интервал',
                    'explanation': 'Для основного текста должен использоваться интервал 1.5.',
                    'paragraph_id': paragraph.id,
                    'preview': paragraph.text[:120],
                    'actual': str(paragraph.line_spacing),
                    'expected': str(EXPECTED_LINE_SPACING),
                    'can_auto_apply': True,
                    'fix_id': fix_id,
                })
                fixes.append({
                    'fix_id': fix_id,
                    'action': 'set_line_spacing',
                    'target_type': 'paragraph',
                    'target_id': paragraph.id,
                    'old_value': str(paragraph.line_spacing),
                    'new_value': str(EXPECTED_LINE_SPACING),
                })
        return issues, fixes


class SpaceBeforeAfterRule(BaseRule):
    rule_id = 'body.space_before_after'
    title = 'Проверка интервала до и после абзаца'

    def check(self, document_model):
        issues = []
        fixes = []
        for paragraph in document_model.paragraphs:
            if paragraph.block_type != 'body' or not paragraph.text.strip():
                continue
            if paragraph.space_before_pt != EXPECTED_SPACE_BEFORE_PT:
                fix_id = uuid4().hex
                issues.append({
                    'issue_id': uuid4().hex,
                    'rule_id': self.rule_id,
                    'severity': self.severity,
                    'message': 'Неверный интервал перед абзацем',
                    'explanation': 'Интервал перед абзацем должен быть 0 pt.',
                    'paragraph_id': paragraph.id,
                    'preview': paragraph.text[:120],
                    'actual': str(paragraph.space_before_pt),
                    'expected': str(EXPECTED_SPACE_BEFORE_PT),
                    'can_auto_apply': True,
                    'fix_id': fix_id,
                })
                fixes.append({
                    'fix_id': fix_id,
                    'action': 'set_space_before',
                    'target_type': 'paragraph',
                    'target_id': paragraph.id,
                    'old_value': str(paragraph.space_before_pt),
                    'new_value': str(EXPECTED_SPACE_BEFORE_PT),
                })
            if paragraph.space_after_pt != EXPECTED_SPACE_AFTER_PT:
                fix_id = uuid4().hex
                issues.append({
                    'issue_id': uuid4().hex,
                    'rule_id': self.rule_id,
                    'severity': self.severity,
                    'message': 'Неверный интервал после абзаца',
                    'explanation': 'Интервал после абзаца должен быть 0 pt.',
                    'paragraph_id': paragraph.id,
                    'preview': paragraph.text[:120],
                    'actual': str(paragraph.space_after_pt),
                    'expected': str(EXPECTED_SPACE_AFTER_PT),
                    'can_auto_apply': True,
                    'fix_id': fix_id,
                })
                fixes.append({
                    'fix_id': fix_id,
                    'action': 'set_space_after',
                    'target_type': 'paragraph',
                    'target_id': paragraph.id,
                    'old_value': str(paragraph.space_after_pt),
                    'new_value': str(EXPECTED_SPACE_AFTER_PT),
                })
        return issues, fixes


class AlignmentRule(BaseRule):
    rule_id = 'body.alignment'
    title = 'Проверка выравнивания'

    def check(self, document_model):
        issues = []
        fixes = []
        for paragraph in document_model.paragraphs:
            if paragraph.block_type != 'body' or not paragraph.text.strip():
                continue
            if not _alignment_ok(paragraph.alignment):
                fix_id = uuid4().hex
                issues.append({
                    'issue_id': uuid4().hex,
                    'rule_id': self.rule_id,
                    'severity': self.severity,
                    'message': 'Неверное выравнивание абзаца',
                    'explanation': 'Основной текст должен быть выровнен по ширине.',
                    'paragraph_id': paragraph.id,
                    'preview': paragraph.text[:120],
                    'actual': str(paragraph.alignment),
                    'expected': EXPECTED_ALIGNMENT,
                    'can_auto_apply': True,
                    'fix_id': fix_id,
                })
                fixes.append({
                    'fix_id': fix_id,
                    'action': 'set_alignment_justify',
                    'target_type': 'paragraph',
                    'target_id': paragraph.id,
                    'old_value': str(paragraph.alignment),
                    'new_value': EXPECTED_ALIGNMENT,
                })
        return issues, fixes
