from brainbox import BrainBox
from brainbox.deciders import Ollama
from typing import Generic, Callable, TypeVar

TCase = TypeVar('TCase')

class LLMPrompter(Generic[TCase]):
    def __init__(self,
                 template: Callable[[TCase], str],
                 model: str,
                 system_prompt: str|None = None
                 ):
        self.template = template
        self.model = model
        self.system_prompt = system_prompt

    def __call__(self, case: TCase) -> BrainBox.ITask:
        prompt = self.template(case)
        return BrainBox.Task.call(Ollama, self.model).question(prompt, system_prompt=self.system_prompt)

