from __future__ import annotations

from abc import ABC, abstractmethod


class BaseRule(ABC):
    rule_id = 'base.rule'
    title = 'Base Rule'
    severity = 'warning'

    @abstractmethod
    def check(self, document_model):
        raise NotImplementedError
