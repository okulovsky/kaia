from typing import Any, Callable

from .step import LLMRequestStep


class CustomPrompt(LLMRequestStep):
    def __init__(self, prompt: Callable[[Any], str]):
        self.prompt = prompt

    def fill_arguments(self, case: Any, template_entities: dict, arguments: dict):
        arguments['prompt'] = self.prompt(case)
