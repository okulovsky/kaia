from .pipeline import TemplateParaphraseCase
from grammatron import Template
from .parsed_template import ParsedTemplate
from copy import deepcopy
from chara.common.descriptions import Language



class TemplateParaphraseCaseManager:
    def __init__(self, cases: list[TemplateParaphraseCase]):
        self.cases = cases

    def prepare(self) -> list[TemplateParaphraseCase]:
        new_cases = []
        for base_case in self.cases:
            for parsed_template in ParsedTemplate.parse(base_case.original_template):
                case = deepcopy(base_case)
                case.parsed_template = parsed_template
                if case.target_language_code is None:
                    case.target_language_code = case.parsed_template.original_language
                case.target_language_name = Language.from_code(case.target_language_code).name
                case.prepare()
                new_cases.append(case)

        return new_cases

    def apply(self, cases: list[TemplateParaphraseCase]) -> list[Template]:
        templates = []
        for case in cases:
            template = case.resulting_template
            template._case = case
            templates.append(template)
        return templates


