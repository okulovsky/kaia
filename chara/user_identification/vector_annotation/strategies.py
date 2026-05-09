from .dto import CurrentState
from ._math import distances_to_classes, closest_class, min_dist_to_samples, l2
from abc import ABC, abstractmethod
import random


class IStrategy(ABC):
    @abstractmethod
    def get_next(self, current_state: CurrentState) -> str | None:
        pass


class BorderlineStrategy(IStrategy):
    def get_next(self, current_state: CurrentState) -> str | None:
        active = {name: vc for name, vc in current_state.classes.items() if vc.center is not None}
        if len(active) < 2:
            return None
        best_id = None
        best_score = float('inf')
        for sample in current_state.free_vectors:
            ranked = distances_to_classes(sample.vector, active)
            score = ranked[1][1] - ranked[0][1]
            if score < best_score:
                best_score = score
                best_id = sample.id
        return best_id


class InsideStrategy(IStrategy):
    def __init__(self, class_: str):
        self.class_ = class_

    def get_next(self, current_state: CurrentState) -> str | None:
        vc = current_state.classes.get(self.class_)
        if vc is None or vc.center is None:
            return None

        active = {name: c for name, c in current_state.classes.items() if c.center is not None}
        region = [s for s in current_state.free_vectors if closest_class(s.vector, active) == self.class_]

        if vc.sigma == 0:
            candidates = region
        else:
            candidates = []
            for multiplier in range(3, 100):
                candidates = [s for s in region if l2(s.vector, vc.center) <= multiplier * vc.sigma]
                if candidates:
                    break

        if not candidates:
            candidates = region or current_state.free_vectors

        return max(candidates, key=lambda s: min_dist_to_samples(s.vector, vc.samples)).id


class RandomStrategy(IStrategy):
    def __init__(self, avoid_classes: tuple[str, ...]):
        self.avoid_classes = avoid_classes

    def get_next(self, current_state: CurrentState) -> str:
        avoid = {
            name: current_state.classes[name]
            for name in self.avoid_classes
            if name in current_state.classes and current_state.classes[name].center is not None
        }
        candidates = current_state.free_vectors
        for multiplier in [3, 2]:
            filtered = [
                s for s in current_state.free_vectors
                if all(l2(s.vector, vc.center) > multiplier * vc.sigma for vc in avoid.values())
            ]
            if filtered:
                candidates = filtered
                break
        return random.choice(candidates).id


class CombinedStrategy(IStrategy):
    def __init__(self, tolerate_difference: int = 5, minimal_amount: int = 5):
        self.tolerate_difference = tolerate_difference
        self.minimal_amount = minimal_amount

    def get_strategy(self, current_state: CurrentState) -> IStrategy:
        counts = {name: len(vc.samples) for name, vc in current_state.classes.items()}
        full_classes = tuple(name for name, n in counts.items() if n >= self.minimal_amount)

        if len(full_classes) < len(current_state.class_names):
            return RandomStrategy(avoid_classes=full_classes)

        smallest = min(counts, key=counts.get)
        biggest = max(counts, key=counts.get)
        if counts[biggest] - counts[smallest] > self.tolerate_difference:
            return InsideStrategy(class_=smallest)

        return BorderlineStrategy()

    def get_next(self, current_state: CurrentState) -> str | None:
        return self.get_strategy(current_state).get_next(current_state)
