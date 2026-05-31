
from dataclasses import dataclass, field
from .standardizer import Standardizer
from .english import english
from .german import german
from .russian import russian
from typing import Callable


_REPlACEMENTS = {
    '"': '“”«»„',
    "'": '‘’`',
    '-': '–—−'
}


@dataclass
class Language:
    code: str
    name: str
    words_symbols: set[str] = field(default_factory=set)
    sentence_symbols: set[str] = field(default_factory=lambda: set(',.-'))
    typographic_replacements: dict[str, str] = field(default_factory=lambda: _REPlACEMENTS)
    sample_text: tuple[str, ...] = ()
    native_espeak_phonemes: set[str]|None = None
    upsampling_dataset_reader: Callable[[], list[str]]|None = None


    @property
    def allowed_symbols(self) -> set[str]:
        return self.words_symbols.union(self.sentence_symbols).union([' '])

    @property
    def standardizer(self) -> Standardizer:
        return Standardizer(self.words_symbols)

    @property
    def espeak_name(self) -> str:
        return self.code

    @property
    def chatterbox_name(self) -> str:
        return self.code

    @property
    def zonos_name(self) -> str:
        return self.code

    @property
    def xtts_name(self) -> str:
        return self.code

    @property
    def vosk_name(self) -> str:
        return self.code

    @staticmethod
    def English() -> 'Language':
        return english()

    @staticmethod
    def German() -> 'Language':
        return german()

    @staticmethod
    def Russian() -> "Language":
        return russian()

    @staticmethod
    def from_code(code: str):
        if code == 'ru':
            return Language.Russian()
        elif code == 'en':
            return Language.English()
        elif code == 'de':
            return Language.German()
        raise ValueError(f"Language {code} is not supported")