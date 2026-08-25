from typing import Any

from .step import LLMRequestStep
from brainbox.deciders import Ollama

class Options(LLMRequestStep):
    def __init__(self, options: Ollama.Options|None = None, **kwargs):
        if kwargs:
            options = options + Ollama.Options(**kwargs)
        self.options = options

    def update_options(self, case: Any, options: Ollama.Options|None) -> Ollama.Options|None:
        if options is None and self.options is None:
            return None
        return options + self.options
