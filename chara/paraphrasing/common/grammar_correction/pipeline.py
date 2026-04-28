from typing import  Any
from pathlib import Path
from chara.common import  logger, BrainBoxCasePipeline, CaseCache, ICase
from chara.common.tools.llm import PromptTaskBuilder, parse_json
from .grammar_model import GrammarModel
from grammatron import Template
from dataclasses import dataclass

import traceback
from copy import deepcopy


@dataclass
class GrammarCorrectionCase(ICase):
    template: Template
    grammar_model: GrammarModel | None = None
    grammar_reply: Any = None


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
        except Exception:
            case.error = f"Can't apply reply {option} to template {case.template}: {traceback.format_exc()}"


    def __call__(self, cache: CaseCache[GrammarCorrectionCase], cases: list[GrammarCorrectionCase]):
        active_cases = []
        result = []
        for case in cases:
            if case.grammar_model is None or len(case.grammar_model.parsed_template.fragments)==0:
                result.append(case)
            else:
                active_cases.append(case)

        subcache = cache.create_subcache('llm')
        @logger.phase(subcache)
        def _():
            pipe = BrainBoxCasePipeline(self.task_builder, self._merge)
            pipe(subcache, active_cases)

        result.extend(subcache.read_cases())
        cache.write_result(result)




