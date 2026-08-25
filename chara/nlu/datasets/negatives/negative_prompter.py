from dataclasses import dataclass
from pathlib import Path
from chara.common.llm import ILLM, LLMRequest
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


def create_negative_request(
        source: ILLM,
        n_phrases: int = 20,
        custom_template_path: Path | None = None,
) -> LLMRequest[NegativeCase, str]:
    path = Path(__file__).parent / 'negative_template.jinja'
    if custom_template_path is not None:
        path = custom_template_path

    def to_jinja_model(case: NegativeCase) -> _NegativeJinjaModel:
        return _NegativeJinjaModel(
            language=_LANGUAGE_NAMES.get(case.language, case.language),
            n_phrases=n_phrases,
        )

    return source.default().template(path).derived_case(to_jinja_model).to_request()
