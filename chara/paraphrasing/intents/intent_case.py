from dataclasses import dataclass
from ..common import ParsedTemplate
from .modality import Modality


@dataclass
class IntentCase:
    template: ParsedTemplate
    language: str = 'ru'
    modality: Modality | None = None
