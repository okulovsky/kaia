from dataclasses import dataclass
import pandas as pd
from ..phonemization import Phonemization
from ....common import Language
from typing import Iterable

@dataclass
class AlgorithmData:
    id_to_sentence: dict[str, str]
    features: pd.DataFrame
    rejected_phonemes: dict[str, int]

    @staticmethod
    def from_phonemizations(data: Iterable[Phonemization], language: Language, strict: bool = False) -> 'AlgorithmData':
        if language.native_espeak_phonemes is None:
            raise ValueError(f"You must first create a list of native espeak phonemes for language `{language.name}`, to equalify on them. Read the log and set the field `native_espeak_phonemes` to the language")
        id_to_sentence = {}
        rows = []
        rejected_phonemes = {}
        for item in data:
            row = {}
            phonemes = (
                phoneme
                for word_phonemization in item.phonemization
                for phoneme in word_phonemization
            )
            for phoneme in phonemes:
                if phoneme not in language.native_espeak_phonemes:
                    if strict:
                        row = None
                        rejected_phonemes[phoneme] = rejected_phonemes.get(phoneme, 0) + 1
                        break
                else:
                    row[phoneme] = row.get(phoneme, 0) + 1

            if row is not None and item.id not in id_to_sentence:
                id_to_sentence[item.id] = item.text
                for phoneme, count in row.items():
                    rows.append(dict(sentence_id=item.id, feature=phoneme, cnt=count))

        return AlgorithmData(
            id_to_sentence,
            pd.DataFrame(rows),
            rejected_phonemes
        )


@dataclass
class AnnotatedSentence:
    id: str
    text: str
    accepted: bool|None = None

