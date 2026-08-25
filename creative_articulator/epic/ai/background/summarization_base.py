from typing import Any

from brainbox import BrainBox

from .background_processor import IBackgroundProcessor
from chara.common.llm import LLMRequest
from ....common import Node
from dataclasses import dataclass


@dataclass
class Summarization:
    summary: str

class SummarizationBase(IBackgroundProcessor):
    @dataclass
    class Task:
        ready_summary: str | None = None
        brainbox_task: BrainBox.Task | None = None

    def __init__(self, request: LLMRequest):
        self.request = request

    def execute(self, task: Task) -> Any:
        if task.brainbox_task is None:
            return None
        return self.request.engine.execute(task.brainbox_task)

    def apply(self, node: Node, task: Task, result) -> None:
        if result is not None:
            summarization = Summarization(result)
        else:
            summarization = Summarization(task.ready_summary)
        node[Summarization] = summarization
