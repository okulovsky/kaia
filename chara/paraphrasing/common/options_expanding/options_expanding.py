from chara.common import Chara, ICase, CaseCollection
from chara.common.descriptions import Language
from chara.common.llm import BulletPointDivider, ILLM
from dataclasses import dataclass, field
from grammatron import Template, OptionsDub
from ..template_paraphrasing import ParsedTemplate
from pathlib import Path
from typing import Any, Iterable


@dataclass
class OptionExpandingCase(ICase):
    variable_name: str
    existing_options: tuple[str,...]
    target_language_code: str
    target_language_name: str

    def get_key(self) -> str:
        return f'{self.variable_name}, {self.target_language_code}, ' + ', '.join(self.existing_options)

    example_templates: list[str] = field(default_factory=list)

    added_options: tuple[str,...] = ()


class OptionExpanding:
    Case = OptionExpandingCase

    def __init__(self, templates: list[Template]):
        self.templates = templates
        self.key_to_variables: dict[str, list[OptionsDub]] = {}

    def prepare(self) -> CaseCollection[OptionExpandingCase]:
        key_to_case: dict[str, OptionExpandingCase] = {}

        for template in self.templates:
            parsed_template = ParsedTemplate.parse_single(template)
            for variable in parsed_template.variables:
                dub = variable.dub
                if not isinstance(dub, OptionsDub):
                    continue
                values = []
                for v in dub.value_to_strs.values():
                    values.extend(v)
                case = OptionExpandingCase(
                    variable.name,
                    tuple(sorted(values)),
                    parsed_template.original_language,
                    Language.from_code(parsed_template.original_language).name
                )
                key = case.get_key()
                if key not in self.key_to_variables:
                    self.key_to_variables[key] = []
                    key_to_case[key] = case
                if len(key_to_case[key].example_templates) < 5:
                    key_to_case[key].example_templates.append(parsed_template.representation)
                self.key_to_variables[key].append(dub)

        return CaseCollection(key_to_case.values())

    def apply(self, cases: Iterable[OptionExpandingCase]) -> list[Template]:
        for case in cases:
            for dub in self.key_to_variables[case.get_key()]:
                for option in case.added_options:
                    dub.value_to_strs[option] = [option]
        return self.templates


    class Pipeline:
        def __init__(self, source: ILLM[OptionExpandingCase, Any]):
            request = source.default().template(Path(__file__).parent/'prompt.jinja').to_request()
            self.request = request.edit().parse(self._merge).assign('added_options').to_request()

        def _merge(self, case: OptionExpandingCase, options: Any) -> tuple[str,...]:
            return tuple(BulletPointDivider()(options))

        def __call__(self, cases: CaseCollection[OptionExpandingCase]) -> CaseCollection[OptionExpandingCase]:
            pipe = self.request.create_brainbox_pipeline()
            inner_result = Chara.call(pipe.__call__)(cases.successes_collection).raise_if_all_errors()
            return CaseCollection(cases.errors, inner_result)

