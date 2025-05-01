import re
from yo_fluq import *

class Standardizer:
    def __init__(self, word_symbols: set[str], to_lowercase: bool = True):
        self.word_symbols = word_symbols
        self.to_lowercase = to_lowercase

    def standardize_to_tuple(self, text) -> tuple[str, ...]:
        s = ''.join(self.word_symbols)
        words = re.split(f'[^{s}]', text)
        if self.to_lowercase:
            return tuple(w.lower() for w in words if w != '')
        return tuple(w for w in words if w != '')

    def standardize_to_str(self, text) -> str:
        return ' '.join(self.standardize_to_tuple(text))

    def standardize_one_word(self, text) -> str:
        value = self.standardize_to_tuple(text)
        if len(value) != 1:
            raise ValueError(f"Expected exactly one word, but was {value}")
        return value[0]

    def try_standardize_one_word(self, text) -> str|None:
        value = self.standardize_to_tuple(text)
        if len(value) != 1:
            return None
        return value[0]

    @property
    def without_lowercase(self):
        return Standardizer(self.word_symbols, False)