from .step import IStep
from typing import Any, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

@dataclass
class AbstractRepresentationStep(IStep, ABC):
    count: int
    item_to_category: Callable[[Any], Any]
    item_filter: Optional[Callable[[Any], bool]] = None
    item_to_count: Optional[Callable[[Any], int]] = None

    def _add_item_to_dict(self, item, d):
        category = self.item_to_category(item)
        if self.item_to_count is None:
            delta = 1
        else:
            delta = self.item_to_count(item)
        d[category] = d.get(category, 0) + delta

    def process(self, history: list, current: list) -> tuple[list, dict]:
        if len(current) <= self.count:
            selected = current
        else:
            categories_count = {}
            for item in history:
                if self.item_filter is not None and not self.item_filter(item):
                    continue
                self._add_item_to_dict(item, categories_count)
            selected = self.select(current, categories_count)

        categories_count = {}
        for item in selected:
            self._add_item_to_dict(item, categories_count)
        return (selected, categories_count)

    def shorten(self, data):
        return data[0]

    def summarize(self, data) -> str|None:
        return ', '.join(f'{k}: {v}' for k, v in data[1].items())


    @abstractmethod
    def select(self, current, categories_count) -> list:
        pass


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


@dataclass
class ProbabilisticEqualRepresentationStep(AbstractRepresentationStep):
    magnitude: float = 1

    def select(self, current, categories_count) -> list:
        if len(current)<self.count:
            return current

        weights = []
        for item in current:
            category = self.item_to_category(item)
            w = 1 / ( 1+ categories_count.get(category, 0)) ** self.magnitude
            weights.append(w)

        seen = set()
        output = []
        for i in range(self.count):
            while True:
                idx = get_random_weighed_element(weights)
                if idx in seen:
                    continue
                seen.add(idx)
                weights[idx] = 0
                output.append(current[idx])
                break

        return output








