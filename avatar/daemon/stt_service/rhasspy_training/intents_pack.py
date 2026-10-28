from dataclasses import dataclass, field
from grammatron import Template

@dataclass
class IntentsPack:
    context: str
    templates: tuple[Template,...]
    custom_words: dict[str, str] = field(default_factory=dict)
    language: str = 'en'

