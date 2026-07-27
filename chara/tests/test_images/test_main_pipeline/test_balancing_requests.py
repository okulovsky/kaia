from collections import Counter
from unittest import TestCase
from chara.common.descriptions.characters import Character
from chara.images.common import Theme, ImageSetup, ActivityStatistics, ImageSetupStatistics
from chara.images.common.generation.balancing_requests import balancing_requests


def _character(name: str) -> Character:
    return Character(name=name, gender=Character.Gender.Feminine, description='desc')


def _setup(name: str) -> ImageSetup:
    return ImageSetup(_character(name), Theme(location='forest'))


class BalancingRequestsTestCase(TestCase):
    def test_setup_way_behind_gets_priority(self):
        setup_a = _setup('A')
        setup_b = _setup('B')
        stats = [
            ImageSetupStatistics(setup_a, {'x': ActivityStatistics(generated=0)}),
            ImageSetupStatistics(setup_b, {'y': ActivityStatistics(generated=5), 'z': ActivityStatistics(generated=0)}),
        ]

        requests = balancing_requests(stats, budget=1, stratification_fields=('character_name',))

        self.assertEqual(1, len(requests))
        self.assertIs(setup_a, requests[0].setup)
        self.assertEqual('x', requests[0].activity)

    def test_never_reselects_a_generated_activity(self):
        setup_a = _setup('A')
        stats = [ImageSetupStatistics(setup_a, {'x': ActivityStatistics(generated=1)})]

        requests = balancing_requests(stats, budget=5, stratification_fields=('character_name',))

        self.assertEqual([], requests)

    def test_exhausted_setup_does_not_block_others(self):
        setup_a = _setup('A')
        setup_exhausted = _setup('Exhausted')
        stats = [
            ImageSetupStatistics(setup_a, {'x': ActivityStatistics(generated=0)}),
            ImageSetupStatistics(setup_exhausted, {'p': ActivityStatistics(generated=3)}),
        ]

        requests = balancing_requests(stats, budget=5, stratification_fields=('character_name',))

        self.assertEqual(1, len(requests))
        self.assertIs(setup_a, requests[0].setup)

    def test_budget_smaller_than_number_of_setups(self):
        setups = [_setup(name) for name in ('A', 'B', 'C')]
        stats = [
            ImageSetupStatistics(setup, {'only': ActivityStatistics(generated=0)})
            for setup in setups
        ]

        requests = balancing_requests(stats, budget=2, stratification_fields=('character_name',))

        self.assertEqual(2, len(requests))
        picked_setups = [r.setup for r in requests]
        self.assertEqual(len(picked_setups), len(set(id(s) for s in picked_setups)))
        for r in requests:
            self.assertEqual('only', r.activity)

    def test_budget_larger_than_available_activities(self):
        setup_a = _setup('A')
        stats = [ImageSetupStatistics(setup_a, {'x': ActivityStatistics(generated=0)})]

        requests = balancing_requests(stats, budget=10, stratification_fields=('character_name',))

        self.assertEqual(1, len(requests))

    def test_empty_stats(self):
        self.assertEqual([], balancing_requests([], budget=10, stratification_fields=('character_name',)))

    def test_recomputes_deserving_setups_across_rounds(self):
        setups = [_setup(name) for name in ('A', 'B', 'C')]
        stats = [
            ImageSetupStatistics(setup, {'a1': ActivityStatistics(generated=0), 'a2': ActivityStatistics(generated=0)})
            for setup in setups
        ]

        requests = balancing_requests(stats, budget=4, stratification_fields=('character_name',))

        self.assertEqual(4, len(requests))
        counts = Counter(r.setup.character.name for r in requests)
        # Round 1 gives every setup its one pick (3 requests); round 2 only has budget
        # for one more, so exactly one setup - recomputed as tied again - gets both of
        # its activities while the other two stay at one.
        self.assertEqual([1, 1, 2], sorted(counts.values()))

    def test_tie_breaks_are_randomized(self):
        setups = [_setup(name) for name in ('A', 'B', 'C')]

        def _stats():
            return [
                ImageSetupStatistics(setup, {'only': ActivityStatistics(generated=0)})
                for setup in setups
            ]

        winners = {balancing_requests(_stats(), budget=1, stratification_fields=('character_name',))[0].setup.character.name for _ in range(30)}

        self.assertGreater(len(winners), 1)
