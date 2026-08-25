from chara.common import Chara, ICase, CaseCollection
from chara.common.llm import BulletPointDivider, LLMRequest
from .parsed_template import ParsedTemplate
from grammatron import Template

class ParaphraseCase(ICase):
    def __init__(self, template: Template, target_language_code: str|None = None):
        self.original_template = template
        self.target_language_code: str|None = target_language_code
        self.target_language_name: str|None = None
        self.parsed_template: ParsedTemplate|None = None
        self.resulting_template: Template|None = None

    def prepare(self):
        pass

class TemplateParaphrase:
    Case = ParaphraseCase

    class Pipeline:
        def __init__(self, request: LLMRequest[ParaphraseCase, Template]):
            # The caller owns the template here, the pipeline only owns the parsing,
            # so there is no default to pre-empt and no reason to go through default().
            if not isinstance(request, LLMRequest):
                raise ValueError(
                    f"TemplateParaphrase.Pipeline has no prompt of its own and needs a "
                    f"fully configured LLMRequest, but got {type(request)}"
                )
            self.request = (request
                            .edit()
                            .parse(self._merge, BulletPointDivider())
                            .assign('resulting_template')
                            .to_request())

        def _merge(self, case: ParaphraseCase, option: str) -> Template:
            return case.parsed_template.restore_template(option, case.target_language_code)

        def __call__(self, cases: CaseCollection[ParaphraseCase]) -> CaseCollection[ParaphraseCase]:
            # One phase, not two: Chara.call caches the raw answers inside the pipeline,
            # so re-running the merge does not re-call the LLM.
            pipe = self.request.create_brainbox_pipeline()
            result = Chara.call(pipe.__call__, 'llm')(cases.successes_collection).raise_if_all_errors()
            return CaseCollection(cases.errors, result)
