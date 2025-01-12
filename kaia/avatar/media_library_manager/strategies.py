from  dataclasses import dataclass

import numpy as np
from abc import ABC, abstractmethod
from brainbox import MediaLibrary



def get_random_weighed_element(elements) -> int:
    csum = []
    for element in elements:
        if len(csum) == 0:
            csum.append(element)
        else:
            csum.append(csum[-1]+element)
    rnd = np.random.rand()*csum[-1]
    for i, cs in enumerate(csum):
        if cs > rnd:
            return i
    return len(csum) - 1




class IContentStrategy(ABC):
    @abstractmethod
    def choose_filename(self, ml: MediaLibrary) -> str | None:
        pass

    def ensure(self, df, *required_columns):
        for column in required_columns:
            if column not in df.columns:
                df[column] = 0
            else:
                df[column] = df[column].fillna(0)



class NewContentStrategy(IContentStrategy):
    def __init__(self, randomize: bool = True):
        self.randomize = randomize

    def choose_filename(self, ml: MediaLibrary) -> str|None:
        df = ml.to_df()
        if df.shape[0] == 0:
            return None
        self.ensure(df, 'feedback_bad', 'feedback_seen')
        df = df.loc[df.feedback_bad==0]
        if df.shape[0] == 0:
            return None
        min_seen = df.feedback_seen.min()
        df = df.loc[df.feedback_seen == min_seen]

        if self.randomize:
            return df.sample(1).filename.iloc[0]
        else:
            return df.filename.iloc[0]

class GoodContentStrategy(IContentStrategy):
    def choose_filename(self, ml: MediaLibrary) -> str | None:
        df = ml.to_df()
        if df.shape[0] == 0:
            return None
        self.ensure(df, 'feedback_bad', 'feedback_seen', 'feedback_good')
        df = df.loc[df.feedback_bad==0]
        df = df.loc[df.feedback_seen>0]
        if df.shape[0] == 0:
            return None
        df['weight'] = df.feedback_good+df.feedback_seen
        num = get_random_weighed_element(df.weight)
        return df.filename.iloc[num]


class AnyContentStrategy(IContentStrategy):
    def choose_filename(self, ml: MediaLibrary) -> str | None:
        df = ml.to_df()
        if df.shape[0] == 0:
            return None
        return df.sample(1).filename.iloc[0]


class SequentialStrategy(IContentStrategy):
    def __init__(self, *strategies):
        self.strategies = strategies

    def choose_filename(self, ml: MediaLibrary) -> str | None:
        for s in self.strategies:
            result = s.choose_filename(ml)
            if result is not None:
                return result
        return None


class WeightedStrategy:
    @dataclass
    class Item:
        strategy: IContentStrategy
        weight: float

    def __init__(self, *weighted_strategies: 'WeightedStrategy.Item'):
        self.random_strategies = weighted_strategies

    def choose_filename(self, ml: MediaLibrary) -> str | None:
        random_strategy = get_random_weighed_element([s.weight for s in self.random_strategies])
        result = self.random_strategies[random_strategy].strategy.choose_filename(ml)
        return result


