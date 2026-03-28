from dataclasses import dataclass
from pathlib import Path
from yo_fluq import FileIO
from foundation_kaia.prompters import JinjaPrompter
from .intent_case import IntentCase

_LANGUAGE_NAMES = {
    'ru': 'Russian',
    'en': 'English',
    'de': 'German',
    'fr': 'French',
}


@dataclass
class _IntentJinjaModel:
    samples: tuple[str, ...]
    variables_description: tuple[str, ...]
    modality: object  # Modality | None
    language: str


class IntentPrompter:
    def __init__(self, custom_template_path: Path | None = None):
        path = Path(__file__).parent / 'intent_template.jinja'
        if custom_template_path is not None:
            path = custom_template_path
        template_text = FileIO.read_text(path)
        self.template = JinjaPrompter(template_text)

    def __call__(self, case: IntentCase) -> str:
        samples = tuple(seq.representation for seq in case.template.sequences)
        variables_description = tuple(
            c.description
            for c in case.template.sequences[0].unwrapped_sequence.fragment_to_description.values()
        )
        model = _IntentJinjaModel(
            samples=samples,
            variables_description=variables_description,
            modality=case.modality,
            language=_LANGUAGE_NAMES.get(case.language, case.language),
        )
        return self.template(model)
