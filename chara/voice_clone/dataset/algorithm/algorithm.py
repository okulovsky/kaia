import numpy as np
import pandas as pd

from .data import AlgorithmData, AnnotatedSentence
from ....common import logger


class Algorithm:
    def __init__(self, data: AlgorithmData):
        self.data = data
        self.id_to_sentence: dict[str, str]|None = None
        self.pdf: pd.DataFrame|None = None
        self.all_features: pd.DataFrame|None = None

    def _compute_estimation(self, sentences):
        xdf = self.pdf
        if sentences is not None:
            xdf = xdf.loc[xdf.sentence_id.isin(sentences)]
        xdf = xdf.groupby('feature').cnt.sum().to_frame()
        xdf = self.all_features.merge(xdf, left_index=True, right_index=True, how='left')
        xdf.cnt = xdf.cnt.fillna(0)
        e = xdf.cnt
        e = np.exp(1 - e / e.max())
        return e

    def _compute_values(self, estimation, exclude):
        edf = self.pdf.assign(value = self.pdf.feature.map(estimation.to_dict()))
        edf = edf.loc[~edf.sentence_id.isin(exclude)]
        edf['bonus'] = edf.value == edf.value.max()
        edf.value *= edf.cnt

        good_sentences = set(edf.loc[edf.bonus].sentence_id)
        kdf = edf.loc[edf.sentence_id.isin(good_sentences)]
        s = kdf.groupby('sentence_id').value.sum().sort_values() / kdf.groupby('sentence_id').cnt.sum()
        return s.sort_values()

    def run(self,
            n_steps: int,
            rejected_sentences_ids: list[str],
            accepted_sentences_ids: list[str],
            banned_words: set[str]
            ):

        banned_words = set(v.lower() for v in banned_words)

        self.id_to_sentence = {
            k:v
            for k, v in self.data.id_to_sentence.items()
            if k not in rejected_sentences_ids
            and not any(w in v.lower() for w in banned_words)
        }
        excluded_ids = set(rejected_sentences_ids) | (self.data.id_to_sentence.keys() - self.id_to_sentence.keys())
        self.pdf = self.data.features.loc[~self.data.features.sentence_id.isin(excluded_ids)]
        self.all_features = (
            self.pdf.feature.drop_duplicates().reset_index(drop=True).to_frame().set_index('feature')
        )

        estimation = self._compute_estimation(None)
        sentences: list[str] = list(accepted_sentences_ids)
        result_begin = len(sentences)
        for i in range(n_steps):
            s = self._compute_values(estimation, sentences)
            s = s.loc[~s.index.isin(sentences)]
            if len(s) == 0:
                break
            idx = s.index[-1]
            sentences.append(idx)
            logger.log(f'{idx}: {self.id_to_sentence[sentences[-1]]}')
            estimation = self._compute_estimation(sentences)

        algorithm_output = [
            AnnotatedSentence(id=i, text=self.id_to_sentence[i])
            for i in sentences[result_begin:]
        ]
        return algorithm_output




