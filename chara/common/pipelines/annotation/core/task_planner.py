from .annotation_cache import AnnotationStatus
from .annotator import TCache
from typing import Generic, Any, TypeVar
from abc import ABC, abstractmethod

TTask = TypeVar('TTask')

class ITaskPlanner(Generic[TCache, TTask], ABC):
    @abstractmethod
    def setup(self, cache: TCache, tasks: dict[str, TTask]):
        ...

    @abstractmethod
    def get_next(self):
        ...


class SimpleTaskPlanner(Generic[TCache, TTask], ITaskPlanner[TCache, TTask]):
    def __init__(self):
        self.cache: TCache|None = None

    def setup(self, cache: TCache, tasks: dict[str, Any]):
        self.cache: TCache = cache
        self.tasks = tasks

    def get_next(self):
        statuses = self.cache.get_annotation_status()
        annotated = set()
        id_to_skip = {}
        for id, s in statuses.items():
            if s.annotated:
                annotated.add(id)
            id_to_skip[id] = s.skipped_times

        free_ids = [id for id in self.tasks if id not in annotated]
        if len(free_ids) == 0:
            return None
        free_id_to_skip = {id: id_to_skip.get(id, 0) for id in free_ids}
        prio = min(free_id_to_skip.values(), default=0)
        free_ids = [i for i in free_ids if id_to_skip.get(i,0) == prio]
        return free_ids[0]



