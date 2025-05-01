from dataclasses import dataclass
import re
from ....tools import Language
from .corpus_filter import ICorpusFilter


@dataclass
class TypographicReplacement(ICorpusFilter):
    replacements: dict[str, str]

    def filter(self, s: str) -> str|None:
        for target, alternatives in self.replacements.items():
            s = re.sub('['+alternatives+']', target, s)
        return s

    @staticmethod
    def from_language(l: Language):
        return TypographicReplacement(l.typographic_replacements)

@dataclass
class BadSymbolsFilter(ICorpusFilter):
    allowed_symbols: set[str]

    def filter(self, s: str) -> str|None:
        for c in s:
            if c not in self.allowed_symbols:
                return None
        return s

    @staticmethod
    def from_language(l: Language):
        return BadSymbolsFilter(l.allowed_symbols)

@dataclass
class LengthFilter(ICorpusFilter):
    min_length: int = 80
    max_length: int = 100

    def filter(self, s: str) -> str|None:
        if len(s)<self.min_length or len(s)>self.max_length:
            return None
        return s


@dataclass
class TooMuchCapitalLettersFilter(ICorpusFilter):
    max_capital_letters: int = 4

    def filter(self, s: str) -> str|None:
        t = s.lower()
        cnt = 0
        for c1, c2 in zip(s, t):
            if c1 != c2:
                cnt += 1
        if cnt>self.max_capital_letters:
            return None
        return s


@dataclass
class NoAbbreviationsFilter(ICorpusFilter):
    word_symbols: set[str]

    def filter(self, s: str) -> str|None:
        t = s.lower()
        word_break = True
        for small, original in zip(s, t):
            is_big = original!=small
            if is_big and not word_break:
                return None
            word_break = original not in self.word_symbols
        return s

    @staticmethod
    def from_language(l: Language):
        return NoAbbreviationsFilter(l.words_symbols)





