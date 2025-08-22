import pandas as pd
from yo_fluq import *

class SimilarityComputer:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer('distiluse-base-multilingual-cased-v1')

    def table_to_list(self, ddf, N: int = 5):
        pdf = ddf.loc[ddf.order < N].pivot_table(index='w1', columns='order', values='w2', aggfunc=lambda z: z)
        return {z[0]: list(z[1]) for z in pdf.iterrows()}

    def compute_table(self, words: list[str]):
        from sentence_transformers import util
        embeddings = self.model.encode(words, convert_to_tensor=True)
        cosine_scores = util.cos_sim(embeddings, embeddings).cpu().numpy()
        rows = []
        for w1 in range(len(words)):
            for w2 in range(len(words)):
                rows.append(dict(w1=words[w1], w2=words[w2], dst=cosine_scores[w1][w2]))
        ddf = pd.DataFrame(rows)
        ddf = ddf.loc[ddf.w1 != ddf.w2]
        ddf = ddf.feed(fluq.add_ordering_column('w1', ('dst', False)))
        return ddf




