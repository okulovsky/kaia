from pathlib import Path
from brainbox import BrainBox
from chara.common.llm import ILLM, LLMRequest
from .case import SelectionCase

class WritingAi:
    Expand = 'expand'

    def __init__(self,
                 expand_request: ILLM,
                 ):
        self.expand_request = (expand_request
                               .default()
                               .template(Path(__file__).parent / 'expand_selection.jinja')
                               .to_request())


    def get_request(self, action: str) -> LLMRequest:
        if action == WritingAi.Expand:
            return self.expand_request
        raise ValueError(f'Unknown action {action}')

    def build_prompt(self, case: SelectionCase, action: str) -> str:
        return self.get_request(action).build_prompt(case)

    def create_task(self, case: SelectionCase, action: str) -> BrainBox.Task:
        return self.get_request(action).create_task(case)

    def run(self, task: BrainBox.Task, action: str) -> str:
        return self.get_request(action).engine.execute(task)
