from typing import Any

from brainbox import BrainBox

from .llm_engine import ILLMEngine


class BrainBoxLLMEngine(ILLMEngine):
    def __init__(self, debug: bool = False):
        self.debug = debug

    @property
    def api(self) -> BrainBox.Api:
        from ...architecture import Chara
        return Chara.Apis.brainbox_api

    def start(self, task: BrainBox.Task) -> Any:
        self.report_task(task)
        return self.api.add(task)

    def join(self, token: Any) -> str:
        result = self.api.join(token)
        self.report_answer(result)
        return result
