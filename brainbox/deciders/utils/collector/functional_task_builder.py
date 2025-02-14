from typing import *
from yo_fluq import Queryable
from .task_builder import TaskBuilder, IBrainBoxTask

class FunctionalTaskBuilder:
    def __init__(self, *selectors: Callable, method: str='to_media_library', to_tags: Optional[Callable] = None):
        self.selectors = selectors
        self.method = method
        self.to_tags = to_tags

    def __call__(self, queryable: Queryable):
        builder = TaskBuilder()
        to_tags = self.to_tags
        if to_tags is None:
            to_tags = lambda z: z
        for element in queryable:
            task = element
            for selector in self.selectors:
                task = selector(task)
            if not isinstance(task, IBrainBoxTask):
                raise ValueError(f"After all selectors, BrainBoxTask was expected, but was {task}")
            builder.append(task, to_tags(element))
        return builder.to_collector_pack(self.method)