from .architecture import AbstractRepresentationStep, RepresentationData
import numpy as np
from dataclasses import dataclass


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

    def select(self, data: list[RepresentationData]) -> None:
        weights = []
        for item in data:
            w = 1 / ( 1+ item.category_size) ** self.magnitude
            weights.append(w)

        seen = set()
        output = []
        for i in range(self.count):
            while True:
                idx = get_random_weighed_element(weights)
                if idx in seen:
                    continue
                data[idx].selected = True
                weights[idx] = 0
                break




