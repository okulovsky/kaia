from ...tools import Standardizer
from yo_fluq import *

class ForeignWordFixer:
    def __init__(self, standardizer: Standardizer):
        self.standardizer = standardizer

    def get_capitalized_and_not_capitalized_words(self, strings: list[str]) -> tuple[set[str], set[str]]:
        st = self.standardizer.without_lowercase
        capitalized_words = set()
        non_capitalized_words = set()
        for s in strings:
            for w in st.standardize_to_tuple(s):
                if w[0].lower() != w[0]:
                    capitalized_words.add(w)
                else:
                    non_capitalized_words.add(w)
        capitalized_words = set(w for w in capitalized_words if w.lower() not in non_capitalized_words)
        return capitalized_words, non_capitalized_words

    def get_words_statistics(self, words, N: int = 10):
        from langdetect import detect_langs
        rows = []
        for w in Query.en(words).feed(fluq.with_progress_bar()):
            row = dict(word=w)
            for i in range(N):
                for l in detect_langs(w):
                    row[l.lang] = row.get(l.lang, 0) + l.prob
            rows.append(row)
        df = pd.DataFrame(rows).fillna(0).set_index('word')
        df = df.div(df.sum(axis=1), axis=0)
        return df

    def standardize_words(self, words):
        return [self.standardizer.standardize_one_word(w) for w in words]



