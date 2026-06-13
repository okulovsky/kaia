from typing import Callable, TypeVar, Generic
from brainbox import BrainBox
from brainbox.deciders import Ollama
from .jinja_prompter import JinjaPrompter
from pathlib import Path


T = TypeVar('T')

class PromptTaskBuilder(Generic[T]):
    def __init__(self,
                 model: str,
                 prompter: Path|str|Callable[[T], str]|None = None,
                 system_prompt: str|None = None,
                 debug: bool = False
                 ):
        self.model = model
        self.system_prompt = system_prompt
        self.debug = debug
        self.prompter = None
        if prompter is not None:
            self.set_prompt(prompter)

    def set_prompt(self, prompter: Path|str|Callable[[T], str], override: bool = False):
        if self.prompter is not None and not override:
            return
        if isinstance(prompter, str) or isinstance(prompter, Path):
            self.prompter = JinjaPrompter(prompter)
        else:
            self.prompter = prompter

    def _get_prompt(self, case) -> str:
        return self.prompter(case)

    def __call__(self, case) -> BrainBox.Task:
        prompt = self._get_prompt(case)
        if self.debug:
            print(prompt)
        return Ollama.new_task(parameter=self.model).question(prompt, self.system_prompt)
