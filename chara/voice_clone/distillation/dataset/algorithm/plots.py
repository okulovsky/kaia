from .data import AlgorithmData, AnnotationCase

def build_statistics_plot(data: AlgorithmData, sentences: list[AnnotationCase]):
    df = data.features
    ids = [s.id for s in sentences if s.accepted]
    df = df.loc[df.sentence_id.isin(ids)]
    df = df.pivot_table(index='sentence_id', columns='feature', values='cnt').fillna(0)
    df = df.loc[ids]
    df.index=list(range(df.shape[0]))

    return df.cumsum().min(axis=1).plot()
