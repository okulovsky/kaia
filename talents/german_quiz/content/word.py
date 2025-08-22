from typing import Any
from dataclasses import dataclass

@dataclass
class Word:
    level: str
    word: str
    wiktionary: str|None = None
    grammar: Any = None
    similar_words: tuple[str,...]|None = None


