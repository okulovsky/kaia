from dataclasses import dataclass
from typing import Callable, Any, TypeVar, Generic
from brainbox import BrainBox
from brainbox.deciders import Ollama
from foundation_kaia.prompters import JinjaPrompter
from pathlib import Path

T = TypeVar('T')

@dataclass
class PromptTaskBuilder(Generic[T]):
    model: str
    prompter: Callable[[T], str] | None = None
    system_prompt: str|None = None
    debug_print: bool = False

    def __call__(self, case) -> BrainBox.Task:
        if self.prompter is None:
            raise ValueError("Prompter was not set")
        prompt = self.prompter(case)
        if self.debug_print:
            print(prompt)
        return Ollama.new_task(parameter=self.model).question(prompt, self.system_prompt)

    def set_default_jinja_prompter(self, file: Path):
        if self.prompter is None:
            self.prompter = JinjaPrompter(file.read_text())

    def set_default_prompter(self, prompter: Callable[[T], str]):
        self.prompter = prompter