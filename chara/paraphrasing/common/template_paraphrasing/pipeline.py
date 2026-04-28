import copy

from chara.common import ICase, CaseCache, logger, BrainBoxCasePipeline, Language
from chara.common.tools.llm import BulletPointDivider, PromptTaskBuilder
import traceback
from .parsed_template import ParsedTemplate
from grammatron import Template
from dataclasses import dataclass

class TemplateParaphraseCase(ICase):
    def __init__(self, template: Template, target_language_code: str|None = None):
        self.original_template = template
        self.target_language_code: str|None = target_language_code
        self.target_language_name: str|None = None
        self.parsed_template: ParsedTemplate|None = None
        self.resulting_template: Template|None = None

    def prepare(self):
        pass





class TemplateParaphrasePipeline:
    def __init__(self, builder: PromptTaskBuilder[TemplateParaphraseCase]):
        self.builder = builder

    def _merge(self, case: TemplateParaphraseCase, option: str):
        try:
            parsed_template = case.parsed_template
            template = parsed_template.restore_template(option, case.target_language_code)
            case.resulting_template = template
        except Exception:
            case.error = f"Option `{option}` failed: {traceback.format_exc()}"

    def __call__(self, cache: CaseCache[TemplateParaphraseCase], cases: list[TemplateParaphraseCase]):

        subcache: CaseCache = cache.create_subcache('llm')
        @logger.phase(subcache, "Running LLM")
        def _():
            pipe = BrainBoxCasePipeline(self.builder, self._merge, BulletPointDivider())
            pipe(subcache, cases)

        result = subcache.read_cases()
        cache.write_result(result)






