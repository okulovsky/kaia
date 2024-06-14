import pandas as pd
from yo_fluq_ds import Query

def count(lst):
    result = {}
    for element in lst:
        result[element] = result.get(element, 0) + 1
    return result


def compute_features_for_row(row):
    result = []
    for feature, cnt in count(['_' + z for z in row.text.lower() if ord(z) <= ord('z') and ord(z) >= ord('a')]).items():
        result.append((row.sentence_id, feature, cnt))
    for feature, cnt in count(row.phonemization.replace(' ', '/').split('/')).items():
        result.append((row.sentence_id, feature, cnt))
    return result


def compute_features(sentences_df, good_phonemes):
    result = []
    for row in Query.df(sentences_df):
        result.extend(compute_features_for_row(row))
    df = pd.DataFrame(result, columns=['sentence_id', 'feature', 'cnt'])
    df = df.loc[df.feature.str.startswith('_') | df.feature.isin(good_phonemes)]
    return df
