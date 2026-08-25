from pathlib import Path
from chara.common.llm import ILLM, LLMRequest
from .uterance_paraphrase_case import UtteranceParaphraseCase


def create_default_utterance_request(
        source: ILLM[UtteranceParaphraseCase, str],
) -> LLMRequest[UtteranceParaphraseCase, str]:
    return source.default().template(Path(__file__).parent/'template.jinja').to_request()
