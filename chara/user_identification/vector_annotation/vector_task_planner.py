import random
from chara.common.pipelines.annotation.core import ITaskPlanner, IAnnotationCache
from .dto import VectorSample, CurrentState, VectorClass, TCase
from typing import Generic
from .strategies import IStrategy, CombinedStrategy


class VectorTaskPlanner(ITaskPlanner[TCase], Generic[TCase]):
    def __init__(self, class_names: tuple[str, ...], strategy: IStrategy|None = None) -> None:
        self.class_names = class_names
        self.vectors: dict[str, VectorSample] | None = None
        self.strategy = strategy if strategy is not None else CombinedStrategy()
        self.cache: IAnnotationCache | None = None

    def setup(self, cache: IAnnotationCache, tasks: list[TCase]):
        self.vectors = {t.get_id(): VectorSample(t.get_vector(), t.get_id()) for t in tasks}
        self.cache = cache

    def _get_state(self) -> CurrentState:
        statuses = self.cache.get_annotation_status()
        assigned: dict[str, list[VectorSample]] = {cn: [] for cn in self.class_names}
        annotated_ids: set[str] = set()
        skipped_ids: set[str] = set()
        for id, status in statuses.items():
            if id not in self.vectors:
                continue
            if status.annotated and status.value in assigned:
                annotated_ids.add(id)
                assigned[status.value].append(self.vectors[id])
                continue
            if status.skipped_times > 0:
                skipped_ids.add(id)

        free = [v for id, v in self.vectors.items() if id not in annotated_ids and id not in skipped_ids]
        classes = {cn: VectorClass.build(cn, samples) for cn, samples in assigned.items()}
        return CurrentState(free_vectors=free, classes=classes, class_names=self.class_names)

    def get_next(self) -> str | None:
        state = self._get_state()
        if not state.free_vectors:
            return None
        result = self.strategy.get_next(state)
        if result is None:
            result = random.choice(state.free_vectors).id
        return result
