from typing import Any

from brainbox import BrainBox

from .llm_engine import ILLMEngine
from .ollama_task_view import OllamaTaskView


class MockLLMEngine(ILLMEngine):
    """Replies with the canned answers in order. The token is the index of the reply."""

    def __init__(self, *replies: str):
        self.replies = replies
        self.tasks: list[OllamaTaskView] = []

    def start(self, task: BrainBox.Task) -> Any:
        self.report_task(task)
        self.tasks.append(OllamaTaskView.parse(task))
        return len(self.tasks) - 1

    def join(self, token: Any) -> str:
        result = self.replies[token]
        self.report_answer(result)
        return result
