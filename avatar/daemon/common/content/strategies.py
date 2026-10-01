import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .record import IRecord
from .feedback import Feedback


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


def _random_element(records: list[IRecord]) -> IRecord:
    return records[np.random.randint(0, len(records))]


class IContentStrategy(ABC):
    @abstractmethod
    def choose(self, records: list[IRecord], feedback: Feedback) -> IRecord|None:
        pass


class NewContentStrategy(IContentStrategy):
    def __init__(self, randomize: bool = True):
        self.randomize = randomize

    def choose(self, records: list[IRecord], feedback: Feedback) -> IRecord|None:
        records = [r for r in records if feedback.get(r.get_id(), 'bad') == 0]
        if len(records) == 0:
            return None
        min_seen = min(feedback.get(r.get_id(), 'seen') for r in records)
        records = [r for r in records if feedback.get(r.get_id(), 'seen') == min_seen]
        return _random_element(records) if self.randomize else records[0]


class GoodContentStrategy(IContentStrategy):
    def choose(self, records: list[IRecord], feedback: Feedback) -> IRecord|None:
        records = [
            r for r in records
            if feedback.get(r.get_id(), 'bad') == 0 and feedback.get(r.get_id(), 'seen') > 0
        ]
        if len(records) == 0:
            return None
        weights = [feedback.get(r.get_id(), 'good') + feedback.get(r.get_id(), 'seen') for r in records]
        return records[get_random_weighed_element(weights)]


class AnyContentStrategy(IContentStrategy):
    def choose(self, records: list[IRecord], feedback: Feedback) -> IRecord|None:
        if len(records) == 0:
            return None
        return _random_element(records)


class SequentialStrategy(IContentStrategy):
    def __init__(self, *strategies: IContentStrategy):
        self.strategies = strategies

    def choose(self, records: list[IRecord], feedback: Feedback) -> IRecord|None:
        for strategy in self.strategies:
            result = strategy.choose(records, feedback)
            if result is not None:
                return result
        return None


class WeightedStrategy(IContentStrategy):
    @dataclass
    class Item:
        strategy: IContentStrategy
        weight: float

    def __init__(self, *weighted_strategies: 'WeightedStrategy.Item'):
        self.weighted_strategies = weighted_strategies

    def choose(self, records: list[IRecord], feedback: Feedback) -> IRecord|None:
        index = get_random_weighed_element([item.weight for item in self.weighted_strategies])
        return self.weighted_strategies[index].strategy.choose(records, feedback)
