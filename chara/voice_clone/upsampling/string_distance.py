import Levenshtein
from dataclasses import dataclass
from typing import Callable, Optional

def transform(s):
    return s.strip().lower().replace('.', '').replace(',', '').replace('-',' ')

@dataclass
class StringDistance:
    additional_transform: Optional[Callable[[str], str]] = None

    def _null_transform(self, s):
        return s

    def __post_init__(self):
        if self.additional_transform is None:
            self.additional_transform = self._null_transform

    def distance(self, s1: str, s2: str) -> int:
        text = transform(s1)
        vosk_text = transform(s2)
        result = Levenshtein.distance(
            self.additional_transform(text),
            self.additional_transform(vosk_text)
        )
        return result

    @staticmethod
    def german_transform(s):
        return s.replace(' ','').replace('-','').replace('ß','ss')





