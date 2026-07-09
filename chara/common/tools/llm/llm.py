from chara import Chara
from chara.common.tools.llm import JinjaPrompter
from pathlib import Path
from brainbox.deciders import Ollama
from chara.common import BrainBoxCaseResultApplicator
from dataclasses import dataclass

@dataclass
class LLMResult:
    result: str|None
    error: str|None = None

class LLM:
    def __init__(self,
                 model: str,
                 system_prompt: str|None = None,
                 debug: bool = False
                 ):
        self.model = model
        self.system_prompt = system_prompt
        self.debug = debug

    def template(self, prompt: Path, case, applicator: BrainBoxCaseResultApplicator|None = None, format: dict|None = None):
        prompt_template = JinjaPrompter(prompt)
        prompt = prompt_template(case)
        if self.debug:
            print(prompt)
        result = Chara.Apis.brainbox_api.execute(Ollama.new_task(parameter=self.model).question(prompt, self.system_prompt, format=format))
        if self.debug:
            print(result)
        if applicator is not None:
            result = applicator.apply_iterable_result([case], [LLMResult(result)])
            if len(result) == 1:
                return result[0]
            else:
                return result
        else:
            return result

