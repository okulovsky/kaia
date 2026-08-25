from typing import Any, Callable

from .step import LLMRequestStep


class DerivedCase(LLMRequestStep):
    """Renders the template against an object derived from the case instead of the case itself."""

    def __init__(self, factory: Callable[[Any], Any], main_field: str = 'case'):
        self.factory = factory
        self.main_field = main_field

    def fill_template_entities(self, case: Any, template_entities: dict):
        template_entities[self.main_field] = self.factory(case)
