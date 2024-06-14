import numpy as np

class GoldenSetAlgorithm:
    def __init__(self, sentences_df, features_df):
        self.sdf = sentences_df
        self.pdf = features_df
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
            banned_sentences_ids: list[int],
            banned_words: list[str],
            print_results: bool = True
            ):
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
        return sentences

    def save_result(self, selected_sentences):
        rdf = self.pdf.loc[self.pdf.sentence_id.isin(selected_sentences)]
        rdf = rdf.pivot_table(index='sentence_id', columns='feature', values='cnt').fillna(0)

        result = []
        for i in selected_sentences:
            result.append(dict(
                text=self.sdf.loc[self.sdf.sentence_id == i].text.iloc[0],
                stats=rdf.loc[i].to_dict()
            ))
        return result


