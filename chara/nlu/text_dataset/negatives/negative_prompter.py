from dataclasses import dataclass
from pathlib import Path
from yo_fluq import FileIO
from foundation_kaia.prompters import JinjaPrompter
from .negative_case import NegativeCase

_LANGUAGE_NAMES = {
    'ru': 'Russian',
    'en': 'English',
    'de': 'German',
    'fr': 'French',
}


@dataclass
class _NegativeJinjaModel:
    language: str
    n_phrases: int


class NegativePrompter:
    def __init__(self, n_phrases: int = 20, custom_template_path: Path | None = None):
        self.n_phrases = n_phrases
        path = Path(__file__).parent / 'negative_template.jinja'
        if custom_template_path is not None:
            path = custom_template_path
        template_text = FileIO.read_text(path)
        self.template = JinjaPrompter(template_text)

    def __call__(self, case: NegativeCase) -> str:
        model = _NegativeJinjaModel(
            language=_LANGUAGE_NAMES.get(case.language, case.language),
            n_phrases=self.n_phrases,
        )
        return self.template(model)
