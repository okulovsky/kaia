from dataclasses import dataclass, field
from .english import english
from .german import german
from .russian import russian
from .standardizer import Standardizer

@dataclass
class Language:
    name: str
    words_symbols: set[str] = field(default_factory=set)
    sentence_symbols: set[str] = field(default_factory=lambda:set(',.-'))
    typographic_replacements: dict[str,str] = field(default_factory=dict)
    sample_text: tuple[str,...] = ()
    native_espeak_phonemes: set[str] = field(default_factory=set)

    @property
    def allowed_symbols(self) -> set[str]:
        return self.words_symbols.union(self.sentence_symbols).union([' '])

    @property
    def standardizer(self) -> Standardizer:
        return Standardizer(self.words_symbols)

    @staticmethod
    def English():
        return english()

    @staticmethod
    def German():
        return german()

    @staticmethod
    def Russian():
        return russian()





