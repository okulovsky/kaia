from typing import Any

from .step import LLMRequestStep

class CaseTypization(LLMRequestStep):
    def __init__(self, case_type: type):
        self.case_type = case_type

    def fill_template_entities(self, case: Any, template_entities: dict):
        if not isinstance(case, self.case_type):
            raise ValueError(f"Expected {self.case_type}, got {type(case)}")
