from .annotation_cache import IAnnotationCache
from .annotator import TCase
from typing import Generic, Any, TypeVar
from abc import ABC, abstractmethod

TTask = TypeVar('TTask')

class ITaskPlanner(Generic[TCase], ABC):
    @abstractmethod
    def setup(self, cache: IAnnotationCache, tasks: list[TCase]):
        ...

    @abstractmethod
    def get_next(self):
        ...


class SimpleTaskPlanner(Generic[TCase], ITaskPlanner[TCase]):
    def __init__(self):
        self.cache: IAnnotationCache|None = None

    def setup(self, cache: IAnnotationCache, cases: list[TCase]):
        self.cache: IAnnotationCache = cache
        self.cases = {c.get_id(): c for c in cases}

    def get_next(self):
        statuses = self.cache.get_annotation_status()
        annotated = set()
        id_to_skip = {}
        for id, s in statuses.items():
            if s.annotated:
                annotated.add(id)
            id_to_skip[id] = s.skipped_times

        free_ids = [id for id in self.cases if id not in annotated]
        if len(free_ids) == 0:
            return None
        free_id_to_skip = {id: id_to_skip.get(id, 0) for id in free_ids}
        prio = min(free_id_to_skip.values(), default=0)
        free_ids = [i for i in free_ids if id_to_skip.get(i,0) == prio]
        return free_ids[0]



