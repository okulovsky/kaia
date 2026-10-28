from collections import Counter
from dataclasses import dataclass
from unittest import TestCase
from foundation_kaia.misc import Loc
from chara.common import Chara, ICase, CaseCollection, CasePrioritization, logger
from chara.common.pipelines.case_prioritization import build_selection_table


@dataclass
class PCase(ICase):
    fingerprint: str
    name: str = ''

    def to_fingerprint(self):
        return self.fingerprint


class InMemoryPrioritization(CasePrioritization[PCase, str]):
    def __init__(self, existing: dict[str, int], usage: dict[str, float]|None = None, **kwargs):
        super().__init__(**kwargs)
        self.existing = existing
        self.usage = usage if usage is not None else {}

    def collect_statistics(self, fingerprints):
        for fingerprint, item in fingerprints.items():
            item.existing = self.existing.get(fingerprint, 0)
            item.usage = self.usage.get(fingerprint)


def cases(*spec: tuple[str, int]) -> CaseCollection[PCase]:
    return CaseCollection([PCase(f, f'{f}{i}') for f, n in spec for i in range(n)])


def run(prioritization: CasePrioritization, collection: CaseCollection, messages: list|None = None) -> CaseCollection:
    with Loc.create_test_folder() as folder:
        Chara.start(folder)
        if messages is None:
            return prioritization(collection)
        with logger.with_callback(lambda item: messages.append(item.to_string())):
            return prioritization(collection)


def selected_counts(result: CaseCollection) -> Counter:
    return Counter(c.fingerprint for c in result.successes)


ONLY_NEW = CasePrioritization.Strategy.only_new
EXPAND = CasePrioritization.Strategy.expand


class CasePrioritizationTestCase(TestCase):
    def test_only_new_takes_all_new_cases(self):
        p = InMemoryPrioritization({'b': 3}, strategy=ONLY_NEW, budget=100)
        result = run(p, cases(('a', 3), ('b', 2), ('c', 1)))
        self.assertEqual(Counter({'a': 3, 'c': 1}), selected_counts(result))

    def test_only_new_budget_cuts(self):
        p = InMemoryPrioritization({}, strategy=ONLY_NEW, budget=4)
        result = run(p, cases(('a', 3), ('b', 3)))
        self.assertEqual(4, len(result.successes))

    def test_only_new_ignores_usage(self):
        p = InMemoryPrioritization({'b': 0}, {'b': 100.0}, strategy=ONLY_NEW, budget=100)
        result = run(p, cases(('a', 1), ('b', 1)))
        self.assertEqual(Counter({'a': 1, 'b': 1}), selected_counts(result))

    def test_cap_only_new(self):
        p = InMemoryPrioritization({}, strategy=ONLY_NEW, budget=100, max_cases_per_fingerprint=2)
        result = run(p, cases(('a', 5), ('b', 1)))
        self.assertEqual(Counter({'a': 2, 'b': 1}), selected_counts(result))

    def test_cap_expand_gives_budget_to_others(self):
        p = InMemoryPrioritization({'b': 10}, strategy=EXPAND, budget=6, max_cases_per_fingerprint=2)
        result = run(p, cases(('a', 5), ('b', 5)))
        self.assertEqual(Counter({'a': 2, 'b': 2}), selected_counts(result))

    def test_no_cap_is_uncapped(self):
        p = InMemoryPrioritization({'b': 10}, strategy=EXPAND, budget=5)
        result = run(p, cases(('a', 5), ('b', 5)))
        self.assertEqual(Counter({'a': 5}), selected_counts(result))

    def _warnings(self, p, collection):
        messages = []
        run(p, collection, messages)
        return [m for m in messages if 'WARNING' in m]

    def test_warning_when_budget_leaves_new_cases(self):
        p = InMemoryPrioritization({}, strategy=ONLY_NEW, budget=3)
        warnings = self._warnings(p, cases(('a', 2), ('b', 2), ('c', 1)))
        self.assertEqual(1, len(warnings))
        self.assertIn('2 new case(s)', warnings[0])

    def test_no_warning_when_cap_leaves_new_cases(self):
        p = InMemoryPrioritization({}, strategy=EXPAND, budget=10, max_cases_per_fingerprint=1)
        self.assertEqual([], self._warnings(p, cases(('a', 3), ('b', 3))))

    def test_no_warning_when_everything_fits(self):
        p = InMemoryPrioritization({}, strategy=ONLY_NEW, budget=10)
        self.assertEqual([], self._warnings(p, cases(('a', 3), ('b', 3))))

    def test_expand_setup_way_behind_gets_priority(self):
        p = InMemoryPrioritization({'a': 0, 'b': 5}, strategy=EXPAND, budget=1)
        result = run(p, cases(('a', 1), ('b', 1)))
        self.assertEqual(Counter({'a': 1}), selected_counts(result))

    def test_expand_evens_out_existing(self):
        p = InMemoryPrioritization({'a': 0, 'b': 2, 'c': 4}, strategy=EXPAND, budget=6)
        result = run(p, cases(('a', 10), ('b', 10), ('c', 10)))
        self.assertEqual(Counter({'a': 4, 'b': 2}), selected_counts(result))

    def test_expand_budget_smaller_than_fingerprints(self):
        p = InMemoryPrioritization({}, strategy=EXPAND, budget=2)
        result = run(p, cases(('a', 1), ('b', 1), ('c', 1)))
        self.assertEqual(2, len(result.successes))
        self.assertEqual(2, len(selected_counts(result)))

    def test_expand_recomputes_after_every_pick(self):
        p = InMemoryPrioritization({}, strategy=EXPAND, budget=4)
        result = run(p, cases(('a', 2), ('b', 2), ('c', 2)))
        self.assertEqual([1, 1, 2], sorted(selected_counts(result).values()))

    def test_expand_tie_breaks_are_randomized(self):
        winners = set()
        for _ in range(30):
            p = InMemoryPrioritization({}, strategy=EXPAND, budget=1)
            winners.update(selected_counts(run(p, cases(('a', 1), ('b', 1), ('c', 1)))))
        self.assertGreater(len(winners), 1)

    def test_effective_existing(self):
        p = InMemoryPrioritization({}, strategy=EXPAND, budget=1)
        self.assertEqual(5, p.effective_existing(5, None))
        self.assertEqual(0, p.effective_existing(0, 10.0))
        self.assertEqual(5, p.effective_existing(5, 3.0))
        self.assertEqual(5, p.effective_existing(5, 5.0))
        self.assertAlmostEqual(1.25, p.effective_existing(5, 20.0))
        self.assertAlmostEqual(61.11, p.effective_existing(110, 198.0), places=2)

    def test_expand_with_usage_prefers_worn_out(self):
        p = InMemoryPrioritization({'small': 5, 'large': 110}, {'small': 20.0, 'large': 198.0}, strategy=EXPAND, budget=1)
        result = run(p, cases(('small', 1), ('large', 1)))
        self.assertEqual(Counter({'small': 1}), selected_counts(result))

    def test_selection_table(self):
        table = build_selection_table([
            (0, 3, 3, 3), (0, 1, 2, 1),
            (1.9, 3.9, 4, 2),
            (3, 3, 1, 0), (4.5, 4.5, 1, 0),
            (5, 5, 1, 0),
            (17, 17, 2, 0),
        ])
        self.assertEqual(['0', '1', '2', '3-4', '5-8', '9-16', '17-32'], [r.label for r in table])
        self.assertEqual([2, 1, 0, 2, 1, 0, 1], [r.fingerprints for r in table])
        self.assertEqual([5, 4, 0, 2, 1, 0, 2], [r.pool for r in table])
        self.assertEqual([4, 2, 0, 0, 0, 0, 0], [r.selected for r in table])
        self.assertEqual([2, 3.9, None, 3.75, 5, None, 17], [r.after for r in table])

    def test_selection_table_empty(self):
        self.assertEqual([], build_selection_table([]))

    def test_several_cases_per_fingerprint_picked_once(self):
        p = InMemoryPrioritization({'b': 100}, strategy=EXPAND, budget=10)
        result = run(p, cases(('a', 3), ('b', 2)))
        self.assertEqual(5, len(result.successes))
        self.assertEqual(5, len(set(c.name for c in result.successes)))

    def test_not_selected_and_errors(self):
        collection = cases(('a', 1), ('b', 1), ('c', 1))
        collection.cases[2].error = 'broken'
        p = InMemoryPrioritization({'b': 1}, strategy=ONLY_NEW, budget=10)
        result = run(p, collection)
        self.assertEqual(['a0', 'b0', 'c0'], [c.name for c in result.cases])
        self.assertEqual([None, CasePrioritization.NOT_SELECTED, 'broken'], [c.error for c in result.cases])
        self.assertIsNone(collection.cases[1].error)

    def test_empty(self):
        p = InMemoryPrioritization({}, strategy=EXPAND, budget=10)
        self.assertEqual(0, len(run(p, CaseCollection([])).cases))
