"""Минимальный smoke-тест структуры проекта."""
from app.rules.registry import get_rules


def test_rules_loaded():
    rules = get_rules()
    assert len(rules) >= 5
