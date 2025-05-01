import numpy as np
import pandas as pd


class GoldenSetAlgorithm:
    def __init__(self, data):
        self.data = data

        sentence_df_rows = []
        features_df_rows = []

        for id, item in data.items():
            sentence_df_rows.append(dict(sentence_id=id, text=item['sentence']))
            for key, value in item['stats'].items():
                features_df_rows.append(dict(sentence_id=id, feature=key, cnt=value))

        self.sdf = pd.DataFrame(sentence_df_rows).set_index('sentence_id')
        self.pdf = pd.DataFrame(features_df_rows)
        self.all_features = self.pdf.feature.drop_duplicates().reset_index(drop=True).to_frame().set_index('feature')

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
            banned_sentences_ids: list[str] = None,
            banned_words: list[str] = None,
            print_results: bool = True
            ):
        if banned_sentences_ids is None:
            banned_sentences_ids = []
        if banned_words is None:
            banned_words = []
        all_banned_sentences = list(banned_sentences_ids)
        for word in banned_words:
            all_banned_sentences.extend(self.sdf.loc[self.sdf.text.str.contains(word)].sentence_id)
        estimation = self._compute_estimation(None)
        sentences = []
        for i in range(n_steps):
            s = self._compute_values(estimation, sentences+banned_sentences_ids)
            s = s.loc[~s.index.isin(sentences) & ~s.index.isin(all_banned_sentences)]
            idx = s.index[-1]
            sentences.append(idx)
            if print_results:
                print(f'{i} {idx}: {self.sdf.loc[idx].text}')
            estimation = self._compute_estimation(sentences)

        algorithm_output = [dict(id=r, index=i, sentence=self.data[r]) for i, r in enumerate(sentences)]
        return algorithm_output




