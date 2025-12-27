from typing import Callable
from ...common import Language
import Levenshtein
from .dto import VerifierResult


class Verifier:
    def __init__(self,
                 language: Language,
                 prefix_max_skip: int = 0,
                 suffix_max_skip: int = 0,
                 max_allowed_distance: int = 0,
                 additional_transform: Callable[[str], str] = None,
                 ):
        self.language = language
        self.prefix_max_skip = prefix_max_skip
        self.suffix_max_skip = suffix_max_skip
        self.additional_transform = additional_transform
        self.max_allowed_distance = max_allowed_distance

    Result = VerifierResult

    def _transform(self, s):
        s = ''.join(c for c in s if c in self.language.words_symbols)
        s = s.lower()
        if self.additional_transform is not None:
            s = self.additional_transform(s)
        return s

    def verify(self, case: str, recognition: list[dict]) -> VerifierResult:
        candidate: VerifierResult|None = None
        for trim_start in range(self.prefix_max_skip+1):
            for trim_end in range(self.suffix_max_skip+1):
                start_index = trim_start
                end_index = len(recognition) - trim_end
                slice = recognition[start_index:end_index]
                s = ''.join(r['word'] for r in slice)
                distance =  Levenshtein.distance(
                    self._transform(case),
                    self._transform(s)
                )
                if candidate is None or candidate.distance > distance:
                    candidate = VerifierResult(
                        distance,
                        slice,
                        slice[-1]['end'] - slice[0]['start'],
                        distance<=self.max_allowed_distance,
                        start_index,
                        end_index,
                        recognition
                    )
        if candidate is None:
            raise ValueError("Cannot be that no candidates are found")
        return candidate





