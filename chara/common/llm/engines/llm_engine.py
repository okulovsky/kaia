from __future__ import annotations
import copy
from abc import ABC, abstractmethod
from brainbox import BrainBox
from typing import Any, TYPE_CHECKING

from .ollama_task_view import OllamaTaskView

if TYPE_CHECKING:
    from ..llm_setup import LLMSetup


class ILLMEngine(ABC):
    debug: bool = False

    @abstractmethod
    def start(self, task: BrainBox.Task) -> Any:
        pass

    @abstractmethod
    def join(self, token: Any) -> str:
        pass

    def execute(self, task: BrainBox.Task) -> str:
        return self.join(self.start(task))

    def with_debug(self, flag: bool = True) -> ILLMEngine:
        """A clone with debugging toggled: a copy, so the api client is shared, not reconnected."""
        result = copy.copy(self)
        result.debug = flag
        return result

    def with_model(self, model: str) -> LLMSetup:
        from ..llm_setup import LLMSetup
        return LLMSetup(self, model)

    def report_task(self, task: BrainBox.Task):
        if not self.debug:
            return
        view = OllamaTaskView.parse(task)
        print('-'*80)
        print(view.model)
        print(view.prompt)

    def report_answer(self, answer: str):
        if not self.debug:
            return
        print(answer)
