from dataclasses import dataclass
from ..common import ParsedTemplate
from .modality import Modality


@dataclass(frozen=True)
class IntentFingerprint:
    template_name: str
    variables_tag: str
    language: str
    modality_name: str | None


@dataclass
class IntentCase:
    template: ParsedTemplate
    language: str = 'en'
    modality: Modality | None = None

    def get_fingerprint(self) -> IntentFingerprint:
        return IntentFingerprint(
            self.template.template.get_name(),
            self.template.variables_tag,
            self.language,
            None if self.modality is None else self.modality.name,
        )
