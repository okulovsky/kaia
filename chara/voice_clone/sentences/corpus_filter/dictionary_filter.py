from ....tools import Standardizer
from .corpus_filter import ICorpusFilter
from pathlib import Path
from yo_fluq import Query

class DictionaryFilter(ICorpusFilter):
    def __init__(self, standardizer: Standardizer, standardized_words: set[str], exclude: bool = False):
        self.standardizer = standardizer
        self.standardized_words = set(standardized_words)
        self.exclude = exclude

    def filter(self, s: str) -> str|None:
        for w in self.standardizer.standardize_to_tuple(s):
            if self.exclude:
                if w in self.standardized_words:
                    return None
            else:
                if w not in self.standardized_words:
                    return None
        return s

    @staticmethod
    def process_vosk_dictionary(file: Path, standardizer: Standardizer) -> set:
        result = set()
        for line in Query.file.text(file, encoding='utf8'):
            word = line.split(' ')[0]
            word = standardizer.try_standardize_one_word(word)
            if word is None:
                continue
            result.add(word)
        return result

