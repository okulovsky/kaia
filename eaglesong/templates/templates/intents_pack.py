from dataclasses import dataclass, field
from .template import Template

@dataclass
class IntentsPack:
    name: str
    templates: tuple[Template,...]
    custom_words: dict[str, str] = field(default_factory=dict)
    language: str = 'en'

