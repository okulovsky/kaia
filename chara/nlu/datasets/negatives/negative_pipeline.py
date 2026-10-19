from chara.common import Chara, CaseCollection
from chara.common.llm import BulletPointDivider, LLMRequest
from .negative_case import NegativeCase


class NegativePipeline:
    """Phrases that are not commands to the assistant: each case asks the LLM for a list of them."""
    def __init__(self, request: LLMRequest[NegativeCase, str]):
        self.request = request

    def _strip(self, case: NegativeCase, text: str) -> str:
        return text.strip()

    def __call__(self, cases: list[NegativeCase]) -> list[str]:
        request = (self.request
                   .edit()
                   .parse(self._strip, BulletPointDivider())
                   .assign('phrase')
                   .to_request())
        pipe = request.create_brainbox_pipeline()
        result = Chara.call(pipe)(CaseCollection(cases))

        seen = set()
        phrases = []
        for case in result.successes:
            text = case.phrase
            if text and text not in seen:
                seen.add(text)
                phrases.append(text)
        return phrases
