from ..step import IStep
from typing import Any, Callable, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np

@dataclass
class RepresentationData:
    item: Any
    category: Any
    category_size: int
    selected: bool


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

    def process(self, history: list, current: list) -> list[RepresentationData]:
        categories_count = {}
        data_list = []
        for item in history:
            if self.item_filter is not None and not self.item_filter(item):
                continue
            category = self.item_to_category(item)
            if self.item_to_count is None:
                delta = 1
            else:
                delta = self.item_to_count(item)
            categories_count[category] = categories_count.get(category, 0) + delta

        for item in current:
            category = self.item_to_category(item)
            data_list.append(RepresentationData(
                item,
                category,
                categories_count.get(category,0),
                False
            ))

        if len(current) < self.count:
            for item in data_list:
                item.selected = True
            return data_list

        self.select(data_list)
        return data_list


    def shorten(self, data):
        return [d.item for d in data if d.selected]


    @abstractmethod
    def select(self, data: list[RepresentationData]) -> None:
        pass

