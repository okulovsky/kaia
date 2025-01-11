from typing import *
from yo_fluq import Queryable
from .task_builder import TaskBuilder, IBrainBoxTask

class FunctionalTaskBuilder:
    def __init__(self, *selectors: Callable, method: str='to_media_library'):
        self.selectors = selectors
        self.method = method

    def __call__(self, queryable: Queryable):
        builder = TaskBuilder()
        for tags in queryable:
            task = tags
            for selector in self.selectors:
                task = selector(task)
            if not isinstance(task, IBrainBoxTask):
                raise ValueError(f"After all selectors, BrainBoxTask was expected, but was {task}")
            builder.append(task, tags)
        return builder.to_collector_pack(self.method)