from dataclasses import dataclass
from typing import Callable, Any
from brainbox import BrainBox
from brainbox.deciders import Ollama

@dataclass
class PromptTaskBuilder:
    prompter: Callable[[Any], str]
    model: str
    system_prompt: str|None = None

    def __call__(self, case) -> BrainBox.ITask:
        prompt = self.prompter(case)
        return BrainBox.Task.call(Ollama, self.model).question(prompt, self.system_prompt)
