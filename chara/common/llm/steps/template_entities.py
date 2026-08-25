from typing import Any

from .step import LLMRequestStep

class TemplateEntities(LLMRequestStep):
    """Extra objects for the template beside the case. A callable value is called on the case."""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def fill_template_entities(self, case: Any, template_entities: dict):
        for k, v in self.kwargs.items():
            template_entities[k] = v(case) if callable(v) else v
