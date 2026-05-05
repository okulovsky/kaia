from typing import Iterable, TypeAlias

from .template_paraphrasing import ParaphraseCase, ParsedTemplate
from grammatron import Template
from copy import deepcopy
from chara.common.descriptions import Language
from .paraphrase_pipeline import ParaphrasePipeline, ParaphrasePipelineSettings
from ...common import CaseCollection


class Paraphrase:
    Case = ParaphraseCase
    Pipeline = ParaphrasePipeline
    Settings = ParaphrasePipelineSettings

    def __init__(self, cases: Iterable[ParaphraseCase]):
        self.cases = list(cases)

    def prepare(self) -> CaseCollection[ParaphraseCase]:
        new_cases = []
        for base_case in self.cases:
            for parsed_template in ParsedTemplate.parse(base_case.original_template):
                case = deepcopy(base_case)
                case.parsed_template = parsed_template
                case.prepare()
                if case.target_language_code is None:
                    case.target_language_code = case.parsed_template.original_language
                case.target_language_name = Language.from_code(case.target_language_code).name
                new_cases.append(case)

        return CaseCollection(new_cases)

    def apply(self, cases: Iterable[ParaphraseCase]) -> list[Template]:
        templates = []
        for case in cases:
            template = case.resulting_template
            template._case = case
            templates.append(template)
        return templates


