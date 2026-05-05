from pathlib import Path
from chara.common import BrainBoxCasePipeline, Chara
from chara.common.tools.llm import PromptTaskBuilder, BulletPointDivider
from .negative_case import NegativeCase


class NegativePipeline:
    def __init__(self, builder: PromptTaskBuilder):
        self.builder = builder

    def _merge(self, case: NegativeCase, text: str):
        case.phrase = text.strip()

    def __call__(self, cases: list[NegativeCase], output_path: Path | None = None) -> list[str]:
        pipe = BrainBoxCasePipeline(self.builder, self._merge, BulletPointDivider())
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
