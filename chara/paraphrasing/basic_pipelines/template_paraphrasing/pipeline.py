import copy

from chara.common import ICache, BrainBoxCache, logger, BrainBoxPipeline, Language
from chara.common.tools.llm import BulletPointDivider, PromptTaskBuilder
from pathlib import Path
import traceback
from typing import Any
from .parsed_template import ParsedTemplate
from grammatron import Template
from dataclasses import dataclass

@dataclass
class TemplateParaphraseCase:
    info: Any
    parsed_template: ParsedTemplate|None

    target_language_code: str|None = None
    target_language_name: str|None = None

    template: Template|None = None



class TemplateParaphraseCache(ICache[list[TemplateParaphraseCase]]):
    def __init__(self, working_directory: Path|None = None):
        super().__init__(working_directory)
        self.llm = BrainBoxCache[TemplateParaphraseCase, TemplateParaphraseCase]()


class TemplateParaphrasePipeline:
    def __init__(self, builder: PromptTaskBuilder[TemplateParaphraseCase]):
        self.builder = builder


    def _merge(self, case: TemplateParaphraseCase, option: str):
        try:
            parsed_template = case.parsed_template
            template = parsed_template.restore_template(option, case.target_language_code)
            new_case = copy.deepcopy(case)
            new_case.template = template
            return new_case
        except Exception as e:
            logger.log(f"Option `{option}` failed")
            logger.log(traceback.format_exc())
            return None

    def __call__(self, cache: TemplateParaphraseCache, cases: list[TemplateParaphraseCase]):
        for case in cases:
            if case.target_language_code is None:
                case.target_language_code = case.parsed_template.original_language
            case.target_language_name = Language.from_code(case.target_language_code).name

        @logger.phase(cache.llm, "Running LLM")
        def _():
            unit = BrainBoxPipeline(
                self.builder,
                self._merge,
                BulletPointDivider(),
            )
            unit.run(cache.llm, cases)

        result = [c for c in cache.llm.read_options() if c is not None]
        cache.write_result(result)






