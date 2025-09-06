from .architecture import AbstractRepresentationStep, RepresentationData
from dataclasses import dataclass

@dataclass
class SortedRepresentationStep(AbstractRepresentationStep):
    def select(self, data: list[RepresentationData]) -> None:
        data = list(sorted(data, key = lambda z: z.category_size))
        for i in range(self.count):
            data[i].selected = True
