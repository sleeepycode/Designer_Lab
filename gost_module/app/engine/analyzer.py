from __future__ import annotations

from app.parser.docx_loader import load_docx
from app.parser.document_parser import parse_document
from app.rules.registry import get_rules


def analyze_document(path: str) -> dict:
    doc = load_docx(path)
    document_model = parse_document(doc)

    issues = []
    fixes = []

    for rule in get_rules():
        rule_issues, rule_fixes = rule.check(document_model)
        issues.extend(rule_issues)
        fixes.extend(rule_fixes)

    return {
        'document_model': document_model.model_dump(),
        'issues': issues,
        'fixes': fixes,
    }
