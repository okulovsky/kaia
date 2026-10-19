import re
from chara.common import Chara, CaseCollection
from chara.common.llm import BulletPointDivider, LLMRequest
from .negative_case import NegativeCase


# Small models number the phrases and add the translations: `15. Ich habe Hunger." (I'm hungry.)`
_NUMBERING = re.compile(r'^\d+[.)]\s*')
_TRANSLATION = re.compile(r'\s*\([^()]*\)\s*$')


class NegativePipeline:
    """Phrases that are not commands to the assistant: each case asks the LLM for a list of them."""
    def __init__(self, request: LLMRequest[NegativeCase, str]):
        self.request = request

    def _strip(self, case: NegativeCase, text: str) -> str:
        text = _NUMBERING.sub('', text.strip())
        text = _TRANSLATION.sub('', text)
        return text.strip().strip('"').strip()

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
