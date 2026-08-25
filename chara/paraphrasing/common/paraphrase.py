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
            # A case that already carries a parsed template has been expanded before, by
            # a caller that needed the parsed template earlier - to build statistics, say.
            # Re-parsing the original would fan it out over every variant a second time,
            # so a batch would arrive larger than it was selected to be, and the variants
            # would be paraphrased and uploaded once per sibling.
            if base_case.parsed_template is not None:
                new_cases.append(self._specialize(base_case, None))
                continue
            for parsed_template in ParsedTemplate.parse(base_case.original_template):
                new_cases.append(self._specialize(base_case, parsed_template))

        return CaseCollection(new_cases)

    def _specialize(self, base_case: ParaphraseCase, parsed_template: ParsedTemplate|None) -> ParaphraseCase:
        case = deepcopy(base_case)
        if parsed_template is not None:
            case.parsed_template = parsed_template
        case.prepare()
        if case.target_language_code is None:
            case.target_language_code = case.parsed_template.original_language
        case.target_language_name = Language.from_code(case.target_language_code).name
        return case

    def apply(self, cases: Iterable[ParaphraseCase]) -> list[Template]:
        templates = []
        for case in cases:
            template = case.resulting_template
            template._case = case
            templates.append(template)
        return templates


