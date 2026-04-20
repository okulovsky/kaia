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
    target_language: str
    parsed_template: ParsedTemplate

    template: Template|None = None
    target_language_name: str|None = None


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
            template = parsed_template.restore_template(option, case.target_language)
            new_case = copy.deepcopy(case)
            new_case.template = template
            return new_case
        except Exception as e:
            logger.log(f"Option `{option}` failed")
            logger.log(traceback.format_exc())
            return None

    def __call__(self, cache: TemplateParaphraseCache, cases: list[TemplateParaphraseCase]):
        for case in cases:
            case.target_language_name = Language.from_code(case.target_language).name

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






