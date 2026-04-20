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



class GrammarCorrectionCache(ICache[list[GrammarCorrectionCase]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.llm = BrainBoxCache[GrammarCorrectionCase, GrammarCorrectionCase]()


class GrammarCorrectionPipeline:
    def __init__(self, language_to_task_builder: dict[str, PromptTaskBuilder[GrammarCorrectionCase]]):
        self.language_to_task_builder = language_to_task_builder
        if 'ru' in self.language_to_task_builder:
            self.language_to_task_builder['ru'].set_default_jinja_prompter(Path(__file__).parent/'ru.jinja')

    def _create_task(self, case: GrammarCorrectionCase):
        return self.language_to_task_builder[case.grammar_model.target_language_code](case)


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
            case = copy.deepcopy(case)
            case.grammar_model = GrammarModel.build(case.template)
            if case.grammar_model.target_language_code in self.language_to_task_builder:
                active_cases.append(case)
            else:
                case.status = CaseStatus.not_required
                result.append(case)

        @logger.phase(cache.llm)
        def _():
            unit = BrainBoxPipeline(self._create_task, self._merge)
            unit.run(cache.llm, active_cases)

        cache.write_result(list(cache.llm.read_options()))

