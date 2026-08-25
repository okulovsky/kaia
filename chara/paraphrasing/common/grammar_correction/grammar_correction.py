from typing import Any, Iterable
from pathlib import Path
from chara.common import Chara, CaseCollection, IVotingCase
from chara.common.llm import ILLM, Json
from .grammar_model import GrammarModel
from grammatron import Template
from dataclasses import dataclass

from copy import deepcopy


@dataclass
class GrammarCorrectionCase(IVotingCase):
    template: Template
    grammar_model: GrammarModel | None = None
    grammar_reply: Any = None

    def get_result_fingerprint(self) -> str:
        if self.grammar_reply is None:
            return ''
        parts = []
        for key, subdict in sorted(self.grammar_reply['grammar'].items()):
            for subkey, value in sorted(subdict.items()):
                parts += [key, subkey, value]
        return '/'.join(parts)


class GrammarCorrection:
    Case = GrammarCorrectionCase

    def __init__(self, templates: list[Template]):
        self.templates = [deepcopy(t) for t in templates]

    def prepare(self) -> CaseCollection[GrammarCorrectionCase]:
        cases = []
        for template in self.templates:
            template = deepcopy(template)
            model = GrammarModel.build(template)
            cases.append(GrammarCorrectionCase(template, model))
        return CaseCollection(cases)

    def apply(self, cases: Iterable[GrammarCorrectionCase]) -> list[Template]:
        return [case.template for case in cases]

    class Pipeline:
        def __init__(self, source: ILLM[GrammarCorrectionCase, Any]):
            request = source.default().template(Path(__file__).parent/'prompt.jinja').to_request()
            self.request = request.edit().parse(self._merge).assign('grammar_reply').to_request()

        def _merge(self, case: GrammarCorrectionCase, option: str) -> Any:
            js = Json.parse_object(option)
            case.grammar_model.apply(js)
            return js

        def __call__(self, cases: CaseCollection[GrammarCorrectionCase]) -> CaseCollection[GrammarCorrectionCase]:
            active_cases = []
            side_cases = []
            for case in cases.cases:
                if case.grammar_model is None or len(case.grammar_model.parsed_template.fragments)==0 or case.error is not None:
                    side_cases.append(case)
                else:
                    active_cases.append(case)

            pipe = self.request.create_brainbox_pipeline()
            inner_result = Chara.call(pipe.__call__)(CaseCollection(active_cases)).raise_if_all_errors()

            return CaseCollection(side_cases, inner_result)





