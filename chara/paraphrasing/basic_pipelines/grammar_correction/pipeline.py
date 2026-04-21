import copy

from chara.common.cache import *
from typing import Generic, TypeVar, Any
from pathlib import Path
from chara.common import BrainBoxCache, logger, BrainBoxPipeline
from chara.common.tools.llm import PromptTaskBuilder, parse_json
from .grammar_model import GrammarModel
from grammatron import Template
from dataclasses import dataclass
from ..utility_pipelines import CaseStatus
import traceback
from copy import deepcopy


@dataclass
class GrammarCorrectionCase:
    template: Template
    grammar_model: GrammarModel | None = None
    grammar_reply: Any = None
    status: CaseStatus = CaseStatus.not_started
    error: str | None = None


class GrammarCorrectionCache(ICache[list[GrammarCorrectionCase]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.llm = BrainBoxCache[GrammarCorrectionCase, GrammarCorrectionCase]()

class GrammarCorrectionCaseManager:
    def __init__(self, templates: list[Template]):
        self.templates = [deepcopy(t) for t in templates]

    def prepare(self) -> list[GrammarCorrectionCase]:
        cases = []
        for template in self.templates:
            template = deepcopy(template)
            model = GrammarModel.build(template)
            cases.append(GrammarCorrectionCase(template, model))
        return cases

    def apply(self, cases: list[GrammarCorrectionCase]) -> list[Template]:
        return [case.template for case in cases]


class GrammarCorrectionPipeline:
    def __init__(self, task_builder: PromptTaskBuilder):
        self.task_builder = task_builder
        if task_builder.case_to_key is None:
            task_builder.case_to_key = lambda case: case.grammar_model.target_language_code
        task_builder.read_default_prompt(Path(__file__).parent/'prompt.jinja')


    def _create_task(self, case: GrammarCorrectionCase):
        return self.task_builder(case)


    def _merge(self, case: GrammarCorrectionCase, option: str):
        try:
            js = parse_json(option)
            case.grammar_reply = js
            case.grammar_model.apply(js)
            case.status = CaseStatus.success
            return case
        except Exception:
            case.status = CaseStatus.error
            case.error = traceback.format_exc()
            logger.log(f"Can't apply reply {option} to template {case.template}")
            return case

    def __call__(self, cache: GrammarCorrectionCache, cases: list[GrammarCorrectionCase]):
        active_cases = []
        result = []
        for case in cases:
            if case.grammar_model is None or len(case.grammar_model.parsed_template.fragments)==0:
                case.status = CaseStatus.not_required
                result.append(case)
            else:
                active_cases.append(case)

        @logger.phase(cache.llm)
        def _():
            unit = BrainBoxPipeline(self._create_task, self._merge)
            unit.run(cache.llm, active_cases)

        result.extend(cache.llm.read_options())
        cache.write_result(result)




