from pathlib import Path
from chara.common import Chara
from chara.common.llm import BulletPointDivider, LLMRequest
from .negative_case import NegativeCase


class NegativePipeline:
    def __init__(self, request: LLMRequest[NegativeCase, str]):
        self.request = request

    def _strip(self, case: NegativeCase, text: str) -> str:
        return text.strip()

    def __call__(self, cases: list[NegativeCase], output_path: Path | None = None) -> list[str]:
        request = (self.request
                   .edit()
                   .parse(self._strip, BulletPointDivider())
                   .assign('phrase')
                   .to_request())
        pipe = request.create_brainbox_pipeline()
        result = Chara.call(pipe)(cases)

        seen = set()
        phrases = []
        for case in result.get_successes():
            text = case.phrase
            if text and text not in seen:
                seen.add(text)
                phrases.append(text)

        if output_path is not None:
            output_path.write_text('\n'.join(phrases), encoding='utf-8')

        return phrases
