from copy import deepcopy

from chara.common import BrainBoxCasePipeline, Chara, ICase, CaseCollection, BrainBoxCaseResultApplicator
from chara.common.tools.llm import BulletPointDivider, PromptTaskBuilder
import traceback
from .parsed_template import ParsedTemplate
from grammatron import Template

class ParaphraseCase(ICase):
    def __init__(self, template: Template, target_language_code: str|None = None):
        self.original_template = template
        self.target_language_code: str|None = target_language_code
        self.target_language_name: str|None = None
        self.parsed_template: ParsedTemplate|None = None
        self.llm_output: str|None = None
        self.resulting_template: Template|None = None

    def prepare(self):
        pass

class TemplateParaphrase:
    Case = ParaphraseCase

    class Pipeline:
        def __init__(self, builder: PromptTaskBuilder[ParaphraseCase]):
            self.builder = builder

        def _merge(self, case: ParaphraseCase, option: str):
            try:
                parsed_template = case.parsed_template
                template = parsed_template.restore_template(option, case.target_language_code)
                case.resulting_template = template
            except Exception:
                case.error = f"Option `{option}` failed: {traceback.format_exc()}"

        def __call__(self, cases: CaseCollection[ParaphraseCase]) -> CaseCollection[ParaphraseCase]:
            pipe = BrainBoxCasePipeline(self.builder, 'llm_output')
            llm_result = Chara.call(pipe.__call__, 'llm')(cases.successes_collection).raise_if_all_errors()

            applicator = BrainBoxCaseResultApplicator(self._merge, BulletPointDivider())
            merge_result = Chara.call(applicator.apply_cached_result, 'merge')(llm_result, 'llm_output')

            return CaseCollection(cases.errors, merge_result)






