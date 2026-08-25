from typing import Any

from .step import LLMRequestStep

class SystemPrompt(LLMRequestStep):
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt

    def fill_arguments(self, case: Any, template_entities: dict, arguments: dict):
        arguments['system_prompt'] = self.system_prompt