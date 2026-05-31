from typing import Any, Iterable
from chara import Language, IAnnotationCase
from dataclasses import dataclass
import pandas as pd
from nltk import word_tokenize

@dataclass
class Phonemization:
    id: str
    text: str
    phonemization: list[list[str]]


@dataclass
class AnnotationCase(IAnnotationCase):
    id: str
    text: str
    accepted: bool|None = None

    def get_id(self) -> str:
        return self.id

    def set_annotation(self, annotation: Any):
        self.accepted = (annotation == 'YES')


def _preprocess_for_samples(language: Language, phonemization: Phonemization, data: dict):
    words = word_tokenize(phonemization.text)
    clean_words = []
    for word in words:
        ok = True
        for c in word:
            if c not in language.words_symbols:
                ok = False
                break
        if ok:
            clean_words.append(word)
    if len(clean_words) != len(phonemization.phonemization):
        return
    for word, p_word in zip(clean_words, phonemization.phonemization):
        for p in p_word:
            if p not in data:
                data[p] = set()
            data[p].add((word, ' '.join(p_word)))


def create_phonemization_samples(
        language: Language,
        phonemizations: Iterable[Phonemization],
        samples_per_phoneme: int = 5):
    data = {}
    for phonemization in phonemizations:
        _preprocess_for_samples(language, phonemization, data)
    rows = []
    for key in data:
        samples = list(data[key])
        rows.append([key, len(samples)])
        for i in range(samples_per_phoneme):
            if i >= len(samples):
                rows[-1].append('')
            else:
                rows[-1].append(' / '.join(samples[i]))
    columns = ['phoneme', 'count'] + [str(i) for i in range(samples_per_phoneme)]
    return pd.DataFrame(rows, columns=columns).sort_values('count', ascending=False).reset_index(
        drop=True)
