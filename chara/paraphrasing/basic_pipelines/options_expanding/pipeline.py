from chara.common import *
from chara.common.tools.llm import PromptTaskBuilder, BulletPointDivider
from dataclasses import dataclass
from grammatron import Template, OptionsDub
from ..template_paraphrasing import ParsedTemplate
from pathlib import Path
from ..utility_pipelines import CaseStatus
import traceback


@dataclass
class OptionExpandingCase:
    variable_name: str
    existing_options: tuple[str,...]
    target_language_code: str
    target_language_name: str

    def get_key(self) -> str:
        return f'{self.variable_name}, {self.target_language_code}, ' + ', '.join(self.existing_options)

    added_options: tuple[str,...] = ()
    status: CaseStatus = CaseStatus.not_started
    error: str|None = None


class OptionExpandingCaseManager:
    def __init__(self, templates: list[Template]):
        self.templates = templates
        self.key_to_variables: dict[str, list[OptionsDub]] = {}


    def prepare(self) -> list[OptionExpandingCase]:
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
                self.key_to_variables[case.get_key()].append(dub)

        return list(key_to_case.values())

    def apply(self, cases: list[OptionExpandingCase]) -> list[Template]:
        for case in cases:
            for dub in self.key_to_variables[case.get_key()]:
                for option in case.added_options:
                    dub.value_to_strs[option] = [option]
        return self.templates


class OptionExpandingCache(ICache[list[OptionExpandingCase]]):
    def __init__(self, working_folder: Path | None = None):
        super().__init__(working_folder)
        self.llm = BrainBoxCache[OptionExpandingCase, OptionExpandingCase]()


class OptionExpandingPipeline:
    def __init__(self, task_builder: PromptTaskBuilder):
        self.task_builder = task_builder
        self.task_builder.read_default_prompt(Path(__file__).parent/'prompt.jinja')

    def _merge(self, case: OptionExpandingCase, options: str):
        try:
            divider = BulletPointDivider()
            case.added_options = tuple(divider(options))
            case.status = CaseStatus.success
        except Exception:
            case.status = CaseStatus.error
            case.error = traceback.format_exc()
        return case

    def __call__(self,
                 cache: OptionExpandingCache,
                 cases: list[OptionExpandingCase]
                 ):
        @logger.phase(cache.llm)
        def _():
            pipe = BrainBoxPipeline(self.task_builder, self._merge)
            pipe.run(cache.llm, cases)

        cache.write_result(list(cache.llm.read_options()))


