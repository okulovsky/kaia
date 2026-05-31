from unittest import TestCase
from unittest.mock import MagicMock
import numpy as np
from chara.user_identification.vector_annotation import (
    VectorSample, VectorClass, CurrentState,
    RandomStrategy, BorderlineStrategy, InsideStrategy, CombinedStrategy,
    VectorTaskPlanner, IVectorAnnotationCase,
)
from chara.common.pipelines.annotation.core import AnnotationStatus


def vec(*coords) -> np.ndarray:
    return np.array(coords, dtype=float)


def sample(id: str, *coords) -> VectorSample:
    return VectorSample(vector=vec(*coords), id=id)


def make_state(
    free: list[VectorSample],
    assigned: dict[str, list[VectorSample]],
    class_names: tuple[str, ...] | None = None,
) -> CurrentState:
    if class_names is None:
        class_names = tuple(assigned.keys())
    classes = {cn: VectorClass.build(cn, samples) for cn, samples in assigned.items()}
    return CurrentState(free_vectors=free, classes=classes, class_names=class_names)


class TestVectorClass(TestCase):
    def test_build_empty(self):
        vc = VectorClass.build('A', [])
        self.assertIsNone(vc.center)
        self.assertEqual(vc.sigma, 0.0)
        self.assertEqual(vc.samples, [])

    def test_build_single_sample(self):
        vc = VectorClass.build('A', [sample('a1', 1.0, 0.0)])
        np.testing.assert_array_almost_equal(vc.center, [1.0, 0.0])
        self.assertEqual(vc.sigma, 0.0)

    def test_build_multiple_samples(self):
        samples_ = [sample('a1', 0.0, 0.0), sample('a2', 2.0, 0.0), sample('a3', 1.0, 0.0)]
        vc = VectorClass.build('A', samples_)
        np.testing.assert_array_almost_equal(vc.center, [1.0, 0.0])
        self.assertGreater(vc.sigma, 0.0)


class TestBorderlineStrategy(TestCase):
    def setUp(self):
        self.state = make_state(
            free=[
                sample('border', 0.0, 0.0),   # equidistant between A and B
                sample('near_a', 0.9, 0.0),    # clearly closer to A
            ],
            assigned={
                'A': [sample('a1', 1.0, 0.0), sample('a2', 1.1, 0.0)],
                'B': [sample('b1', -1.0, 0.0), sample('b2', -1.1, 0.0)],
            },
        )

    def test_picks_borderline_sample(self):
        result = BorderlineStrategy().get_next(self.state)
        self.assertEqual(result, 'border')

    def test_returns_none_when_fewer_than_two_active_classes(self):
        state = make_state(
            free=[sample('f1', 0.0, 0.0)],
            assigned={'A': [sample('a1', 1.0, 0.0)], 'B': []},
        )
        result = BorderlineStrategy().get_next(state)
        self.assertIsNone(result)

    def test_returns_none_when_no_active_classes(self):
        state = make_state(
            free=[sample('f1', 0.0, 0.0)],
            assigned={'A': [], 'B': []},
        )
        result = BorderlineStrategy().get_next(state)
        self.assertIsNone(result)


class TestInsideStrategy(TestCase):
    def setUp(self):
        # A is centered at (1, 0), B at (-1, 0)
        self.state = make_state(
            free=[
                sample('inside_a', 1.0, 0.5),    # closest to A, near center
                sample('inside_b', -1.0, 0.5),   # closest to B
                sample('novel_a', 3.0, 0.0),      # closest to A, far from any A sample
            ],
            assigned={
                'A': [sample('a1', 1.0, 0.0), sample('a2', 1.1, 0.0), sample('a3', 0.9, 0.0)],
                'B': [sample('b1', -1.0, 0.0), sample('b2', -1.1, 0.0), sample('b3', -0.9, 0.0)],
            },
        )

    def test_picks_from_class_a_region(self):
        result = InsideStrategy('A').get_next(self.state)
        self.assertIn(result, ('inside_a', 'novel_a'))

    def test_picks_most_novel_inside_a(self):
        # A has high spread (sigma=1.0, 3sigma=3.0) so both free candidates fall in the sigma window.
        # Strategy must pick the one farthest from any existing A sample.
        state = make_state(
            free=[
                sample('close_a', 0.5, 0.0),  # 0.5 from A center, 0.5 from nearest A sample
                sample('far_a', 2.5, 0.0),     # 2.5 from A center (within 3sigma=3.0), 1.5 from nearest
            ],
            assigned={
                'A': [
                    sample('a1', 1.0, 0.0), sample('a2', -1.0, 0.0),
                    sample('a3', 0.0, 3.0), sample('a4', 0.0, -3.0),
                ],
                'B': [sample('b1', 50.0, 0.0), sample('b2', 51.0, 0.0), sample('b3', 49.0, 0.0)],
            },
        )
        result = InsideStrategy('A').get_next(state)
        self.assertEqual(result, 'far_a')

    def test_returns_none_for_unknown_class(self):
        result = InsideStrategy('C').get_next(self.state)
        self.assertIsNone(result)

    def test_returns_none_for_empty_class(self):
        state = make_state(
            free=[sample('f1', 0.0, 0.0)],
            assigned={'A': [], 'B': [sample('b1', -1.0, 0.0)]},
        )
        result = InsideStrategy('A').get_next(state)
        self.assertIsNone(result)

    def test_falls_back_when_no_region_candidates(self):
        # All free vectors are closer to B than A → falls back to all free vectors
        state = make_state(
            free=[sample('f1', -0.5, 0.0), sample('f2', -0.6, 0.0)],
            assigned={
                'A': [sample('a1', 1.0, 0.0)],
                'B': [sample('b1', -1.0, 0.0)],
            },
        )
        result = InsideStrategy('A').get_next(state)
        self.assertIsNotNone(result)

    def test_sigma_zero_uses_all_region_candidates(self):
        # Single A sample → sigma=0, should still return a result
        state = make_state(
            free=[sample('inside_a', 1.0, 0.5)],
            assigned={
                'A': [sample('a1', 1.0, 0.0)],
                'B': [sample('b1', -1.0, 0.0)],
            },
        )
        result = InsideStrategy('A').get_next(state)
        self.assertEqual(result, 'inside_a')


class TestRandomStrategy(TestCase):
    def test_picks_from_free(self):
        state = make_state(
            free=[sample('f1', 0.0, 0.0), sample('f2', 0.1, 0.0)],
            assigned={'A': [], 'B': []},
        )
        result = RandomStrategy(avoid_classes=()).get_next(state)
        self.assertIn(result, ('f1', 'f2'))

    def test_avoids_class_region(self):
        # A has sigma≈0.236, so 3sigma≈0.71.
        # near_a is 0.2 from A center (within 3sigma) → filtered out.
        # neutral is 10.0 from A center (outside 3sigma) → kept.
        state = make_state(
            free=[
                sample('near_a', 9.8, 0.0),
                sample('neutral', 0.0, 0.0),
            ],
            assigned={
                'A': [sample('a1', 10.0, 0.0), sample('a2', 10.5, 0.0), sample('a3', 9.5, 0.0)],
                'B': [],
            },
        )
        results = {RandomStrategy(avoid_classes=('A',)).get_next(state) for _ in range(20)}
        self.assertNotIn('near_a', results)

    def test_falls_back_to_all_when_all_filtered(self):
        # Free vectors are all very close to avoided class → must still return something
        state = make_state(
            free=[sample('f1', 1.0, 0.0), sample('f2', 1.05, 0.0)],
            assigned={
                'A': [sample('a1', 1.0, 0.0), sample('a2', 1.1, 0.0), sample('a3', 0.9, 0.0)],
            },
        )
        result = RandomStrategy(avoid_classes=('A',)).get_next(state)
        self.assertIn(result, ('f1', 'f2'))


class TestCombinedStrategy(TestCase):
    def _make_state_with_counts(self, count_a: int, count_b: int, free_count: int = 3) -> CurrentState:
        assigned_a = [sample(f'a{i}', 1.0 + i * 0.01, 0.0) for i in range(count_a)]
        assigned_b = [sample(f'b{i}', -1.0 - i * 0.01, 0.0) for i in range(count_b)]
        free = [sample(f'f{i}', 0.0, float(i)) for i in range(free_count)]
        return make_state(free=free, assigned={'A': assigned_a, 'B': assigned_b})

    def test_bootstrap_phase_returns_random_strategy(self):
        # Both classes below minimal_amount=5
        state = self._make_state_with_counts(count_a=2, count_b=3)
        strategy = CombinedStrategy(minimal_amount=5).get_strategy(state)
        self.assertIsInstance(strategy, RandomStrategy)

    def test_bootstrap_avoids_full_classes(self):
        # A has enough, B does not → random strategy should avoid A
        state = self._make_state_with_counts(count_a=5, count_b=2)
        strategy = CombinedStrategy(minimal_amount=5).get_strategy(state)
        self.assertIsInstance(strategy, RandomStrategy)
        self.assertIn('A', strategy.avoid_classes)
        self.assertNotIn('B', strategy.avoid_classes)

    def test_balance_phase_returns_inside_strategy_for_smallest(self):
        # Both classes bootstrapped, but A >> B
        state = self._make_state_with_counts(count_a=10, count_b=5)
        strategy = CombinedStrategy(minimal_amount=5, tolerate_difference=3).get_strategy(state)
        self.assertIsInstance(strategy, InsideStrategy)
        self.assertEqual(strategy.class_, 'B')

    def test_refine_phase_returns_borderline_strategy(self):
        # Both classes bootstrapped and balanced
        state = self._make_state_with_counts(count_a=6, count_b=5)
        strategy = CombinedStrategy(minimal_amount=5, tolerate_difference=3).get_strategy(state)
        self.assertIsInstance(strategy, BorderlineStrategy)

    def test_get_next_returns_string(self):
        state = self._make_state_with_counts(count_a=6, count_b=5)
        result = CombinedStrategy(minimal_amount=5, tolerate_difference=3).get_next(state)
        self.assertIsInstance(result, str)


class TestVectorTaskPlanner(TestCase):
    class _MockCase(IVectorAnnotationCase):
        def __init__(self, id_: str, v: np.ndarray):
            self._id = id_
            self._v = v
            self.annotation = None

        def get_id(self) -> str:
            return self._id

        def get_vector(self) -> np.ndarray:
            return self._v

        def set_annotation(self, annotation):
            self.annotation = annotation

    def _make_cache(self, annotations: dict[str, str]) -> MagicMock:
        cache = MagicMock()
        statuses = {id: AnnotationStatus(value=label) for id, label in annotations.items()}
        cache.get_annotation_status.return_value = statuses
        return cache

    def test_get_next_returns_unannotated(self):
        cases = [
            self._MockCase('c1', vec(1.0, 0.0)),
            self._MockCase('c2', vec(-1.0, 0.0)),
            self._MockCase('c3', vec(0.0, 1.0)),
        ]
        planner = VectorTaskPlanner(
            class_names=('A', 'B'),
            strategy=CombinedStrategy(minimal_amount=2),
        )
        planner.setup(self._make_cache({'c1': 'A'}), cases)
        result = planner.get_next()
        self.assertIn(result, ('c2', 'c3'))

    def test_get_next_returns_none_when_all_annotated(self):
        cases = [self._MockCase('c1', vec(1.0, 0.0))]
        planner = VectorTaskPlanner(
            class_names=('A', 'B'),
            strategy=RandomStrategy(avoid_classes=()),
        )
        planner.setup(self._make_cache({'c1': 'A'}), cases)
        result = planner.get_next()
        self.assertIsNone(result)

    def test_get_next_falls_back_to_random_when_strategy_returns_none(self):
        # BorderlineStrategy returns None when < 2 active classes;
        # planner should fall back to random choice from free vectors
        cases = [
            self._MockCase('c1', vec(1.0, 0.0)),
            self._MockCase('c2', vec(2.0, 0.0)),
        ]
        planner = VectorTaskPlanner(
            class_names=('A', 'B'),
            strategy=BorderlineStrategy(),
        )
        planner.setup(self._make_cache({}), cases)
        result = planner.get_next()
        self.assertIn(result, ('c1', 'c2'))
