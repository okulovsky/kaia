from chara.common import BrainBoxCasePipeline, Chara, ICase, CaseCollection
from chara.common.descriptions import Language
from chara.common.tools.llm import PromptTaskBuilder, BulletPointDivider
from dataclasses import dataclass, field
from grammatron import Template, OptionsDub
from ..template_paraphrasing import ParsedTemplate
from pathlib import Path
import traceback
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
        def __init__(self, task_builder: PromptTaskBuilder):
            self.task_builder = task_builder
            self.task_builder.read_default_prompt(Path(__file__).parent/'prompt.jinja')

        def _merge(self, case: OptionExpandingCase, options: Any) -> None:
            try:
                divider = BulletPointDivider()
                case.added_options = tuple(divider(options))
            except Exception:
                case.error = traceback.format_exc()


        def __call__(self, cases: CaseCollection[OptionExpandingCase]) -> CaseCollection[OptionExpandingCase]:
            pipe = BrainBoxCasePipeline(self.task_builder, self._merge)
            inner_result = Chara.call(pipe.__call__)(cases.successes_collection).raise_if_all_errors()
            return CaseCollection(cases.errors, inner_result)

