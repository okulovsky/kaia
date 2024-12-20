from typing import *
from yo_fluq_ds import Queryable
from .collector_task_builder import CollectorTaskBuilder
from kaia.brainbox import BrainBoxTask

class FunctionalTaskBuilder:
    def __init__(self, *selectors: Callable, method: str='to_media_library'):
        self.selectors = selectors
        self.method = method

    def __call__(self, queryable: Queryable):
        builder = CollectorTaskBuilder()
        for tags in queryable:
            task = tags
            for selector in self.selectors:
                task = selector(task)
            if not isinstance(task, BrainBoxTask):
                raise ValueError(f"After all selectors, BrainBoxTask was expected, but was {task}")
            builder.append(task, tags)
        return builder.to_collector_pack(self.method)