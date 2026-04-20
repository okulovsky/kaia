from chara.common import *
from chara.common.tools.llm import PromptTaskBuilder, BulletPointDivider
from dataclasses import dataclass
from grammatron import Template, OptionsDub
from ..template_paraphrasing import ParsedTemplate
from pathlib import Path

@dataclass(frozen=True)
class OptionExpandingCase:
    variable_name: str
    existing_options: tuple[str,...]
    target_language_code: str
    target_language_name: str


class OptionExpandingCache(ICache[list[Template]]):
    def __init__(self, working_folder: Path|None = None):
        super().__init__(working_folder)
        self.llm = BrainBoxCache[OptionExpandingCase, OptionExpandingCase]()


class OptionExpandingPipeline:
    def __init__(self, task_builder: PromptTaskBuilder):
        self.task_builder = task_builder

    def __call__(self, cache: OptionExpandingCache, templates: list[Template]):
        case_to_variables: dict[OptionExpandingCase, list[OptionsDub]] = {}
        for template in templates:
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
                    tuple(values),
                    parsed_template.original_language,
                    Language.from_code(parsed_template.original_language).name
                )
                if case not in case_to_variables:
                    case_to_variables[case] = []
                case_to_variables[case].append(dub)

        @logger.phase(cache.llm)
        def _():
            pipe = BrainBoxPipeline(self.task_builder)
            pipe.run(cache.llm, list(case_to_variables.keys()))

        divider = BulletPointDivider()
        for case, option in cache.llm.read_cases_and_options():
            lines = divider(option)
            for dub in case_to_variables[case]:
                for line in lines:
                    dub.value_to_strs[line] = [line]

        cache.write_result(templates)