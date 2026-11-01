from collections import Counter
from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara, CaseCollection, CasePrioritization
from chara.common.descriptions.characters import Character
from chara.images.common import Theme, ImageSetup, ActivityStatistics, ImageSetupStatistics, ImageRequest
from chara.images.common.generation import ImagePrioritization


def _character(name: str) -> Character:
    return Character(name=name, gender=Character.Gender.Feminine, description='desc')


def _setup(name: str) -> ImageSetup:
    return ImageSetup(_character(name), Theme(location='forest'))


def _select(stats: list[ImageSetupStatistics],
            budget: int,
            strategy: CasePrioritization.Strategy = CasePrioritization.Strategy.expand,
            max_images_per_group: int|None = None,
            ) -> list[ImageRequest]:
    candidates = [
        ImageRequest(stat.setup, activity)
        for stat in stats
        for activity, activity_stat in stat.activity_status.items()
        if activity_stat.generated == 0
    ]
    prioritization = ImagePrioritization(stats, ('character_name',), strategy, budget, max_images_per_group)
    with Loc.create_test_folder() as folder:
        Chara.start(folder)
        return list(prioritization(CaseCollection(candidates)).successes)


class ImagePrioritizationTestCase(TestCase):
    def test_setup_way_behind_gets_priority(self):
        stats = [
            ImageSetupStatistics(_setup('A'), {'x': ActivityStatistics(generated=0)}),
            ImageSetupStatistics(_setup('B'), {'y': ActivityStatistics(generated=5), 'z': ActivityStatistics(generated=0)}),
        ]

        requests = _select(stats, budget=1)

        self.assertEqual(1, len(requests))
        self.assertEqual('A', requests[0].setup.character.name)
        self.assertEqual('x', requests[0].activity)

    def test_never_reselects_a_generated_activity(self):
        stats = [ImageSetupStatistics(_setup('A'), {'x': ActivityStatistics(generated=1)})]

        self.assertEqual([], _select(stats, budget=5))

    def test_exhausted_setup_does_not_block_others(self):
        stats = [
            ImageSetupStatistics(_setup('A'), {'x': ActivityStatistics(generated=0)}),
            ImageSetupStatistics(_setup('Exhausted'), {'p': ActivityStatistics(generated=3)}),
        ]

        requests = _select(stats, budget=5)

        self.assertEqual(1, len(requests))
        self.assertEqual('A', requests[0].setup.character.name)

    def test_budget_smaller_than_number_of_setups(self):
        stats = [
            ImageSetupStatistics(_setup(name), {'only': ActivityStatistics(generated=0)})
            for name in ('A', 'B', 'C')
        ]

        requests = _select(stats, budget=2)

        self.assertEqual(2, len(requests))
        self.assertEqual(2, len(set(r.setup.character.name for r in requests)))
        for r in requests:
            self.assertEqual('only', r.activity)

    def test_budget_larger_than_available_activities(self):
        stats = [ImageSetupStatistics(_setup('A'), {'x': ActivityStatistics(generated=0)})]

        self.assertEqual(1, len(_select(stats, budget=10)))

    def test_empty_stats(self):
        self.assertEqual([], _select([], budget=10))

    def test_recomputes_after_every_pick(self):
        stats = [
            ImageSetupStatistics(_setup(name), {'a1': ActivityStatistics(generated=0), 'a2': ActivityStatistics(generated=0)})
            for name in ('A', 'B', 'C')
        ]

        requests = _select(stats, budget=4)

        self.assertEqual(4, len(requests))
        counts = Counter(r.setup.character.name for r in requests)
        self.assertEqual([1, 1, 2], sorted(counts.values()))

    def test_tie_breaks_are_randomized(self):
        def _stats():
            return [
                ImageSetupStatistics(_setup(name), {'only': ActivityStatistics(generated=0)})
                for name in ('A', 'B', 'C')
            ]

        winners = {_select(_stats(), budget=1)[0].setup.character.name for _ in range(30)}

        self.assertGreater(len(winners), 1)

    def test_existing_is_summed_over_the_group(self):
        setup_a1 = ImageSetup(_character('A'), Theme(location='forest'))
        setup_a2 = ImageSetup(_character('A'), Theme(location='beach'))
        stats = [
            ImageSetupStatistics(setup_a1, {'x': ActivityStatistics(generated=2), 'p': ActivityStatistics(generated=0)}),
            ImageSetupStatistics(setup_a2, {'y': ActivityStatistics(generated=2), 'q': ActivityStatistics(generated=0)}),
            ImageSetupStatistics(_setup('B'), {'z': ActivityStatistics(generated=3), 'r': ActivityStatistics(generated=0)}),
        ]

        requests = _select(stats, budget=1)

        self.assertEqual('B', requests[0].setup.character.name)

    def test_only_new_skips_groups_with_images(self):
        stats = [
            ImageSetupStatistics(_setup('A'), {'x': ActivityStatistics(generated=0), 'y': ActivityStatistics(generated=0)}),
            ImageSetupStatistics(_setup('B'), {'z': ActivityStatistics(generated=1), 'w': ActivityStatistics(generated=0)}),
        ]

        requests = _select(stats, budget=10, strategy=CasePrioritization.Strategy.only_new)

        self.assertEqual(['A', 'A'], [r.setup.character.name for r in requests])

    def test_max_images_per_group(self):
        stats = [
            ImageSetupStatistics(_setup('A'), {f'a{i}': ActivityStatistics(generated=0) for i in range(5)}),
            ImageSetupStatistics(_setup('B'), {f'b{i}': ActivityStatistics(generated=0) for i in range(5)}),
        ]

        requests = _select(stats, budget=10, max_images_per_group=2)

        self.assertEqual(Counter({'A': 2, 'B': 2}), Counter(r.setup.character.name for r in requests))
