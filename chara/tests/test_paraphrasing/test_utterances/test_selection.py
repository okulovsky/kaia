import unittest
from dataclasses import dataclass

from chara.common import CaseRepetition
from chara.paraphrasing.utterances import DeficitSelection, NewEntitiesSelection
from chara.paraphrasing.utterances.stats_builder import ParaphraseFingerprint, ParaphraseStats


@dataclass
class _Case:
    name: str
    stats: ParaphraseStats = None


def summary(name: str, existing: int = 0, seen: int = 0, successes: int = 0, errors: int = 0):
    fingerprint = ParaphraseFingerprint(name, '', 'en', None, None)
    return CaseRepetition.Summary(
        _Case(name, ParaphraseStats(fingerprint, existing, seen)),
        [object()] * successes,
        [object()] * errors,
    )


def names(selected) -> list[str]:
    return [c.name for c in selected]


class NewEntitiesSelectionTestCase(unittest.TestCase):
    def test_only_the_uncovered_are_taken(self):
        selection = NewEntitiesSelection()
        summaries = [summary('has_some', existing=1), summary('has_none', existing=0)]
        self.assertEqual(['has_none'], names(selection(summaries)))

    def test_a_worn_out_case_is_not_this_selection_business(self):
        selection = NewEntitiesSelection()
        self.assertEqual([], selection([summary('worn', existing=110, seen=198)]))

    def test_the_manager_order_is_kept(self):
        selection = NewEntitiesSelection(batch_size=2)
        self.assertEqual(['a', 'b'], names(selection([summary(n) for n in 'abcd'])))

    def test_cases_already_done_are_skipped(self):
        selection = NewEntitiesSelection()
        self.assertEqual(['b'], names(selection([summary('a', successes=1), summary('b')])))

    def test_a_case_that_keeps_failing_is_given_up_on(self):
        selection = NewEntitiesSelection(max_errors=2)
        self.assertEqual(['ok'], names(selection([summary('spent', errors=2), summary('ok')])))

    def test_no_budget_means_no_limit(self):
        selection = NewEntitiesSelection(batch_size=100)
        summaries = [summary(str(i)) for i in range(300)]
        self.assertEqual(100, len(selection(summaries)))
        self.assertEqual(100, len(selection(summaries)))
        self.assertEqual(100, len(selection(summaries)))

    def test_a_covered_case_is_not_offered_twice(self):
        selection = NewEntitiesSelection()
        covered = summary('covered', existing=0, successes=1)
        self.assertEqual([], selection([covered]))


class DeficitSelectionTestCase(unittest.TestCase):
    def test_the_most_repetitive_goes_first(self):
        # Relative, not absolute: 20/5 is heard 4 times per paraphrase and feels worse
        # than 198/110 at 1.8, even though the latter has served more repeats in total.
        selection = DeficitSelection(batch_size=2)
        summaries = [
            summary('big_but_stocked', existing=110, seen=198),  # 1.8
            summary('small_and_worn', existing=5, seen=20),      # 4.0
            summary('fine', existing=49, seen=22),               # 0.45
        ]
        self.assertEqual(['small_and_worn', 'big_but_stocked'], names(selection(summaries)))

    def test_the_batch_is_always_full(self):
        # Nothing is filtered out, so cases that are not worn yet fill the batch.
        selection = DeficitSelection(batch_size=3)
        summaries = [summary('worn', existing=1, seen=9)] + [summary(n, existing=9, seen=1) for n in 'abcd']
        self.assertEqual(3, len(selection(summaries)))
        self.assertEqual('worn', names(selection(summaries))[0])

    def test_the_budget_is_the_number_of_cases(self):
        # 100 cases means paraphrases for 100 cases, in exactly two full batches.
        selection = DeficitSelection(budget=100, batch_size=50)
        summaries = [summary(str(i), existing=5, seen=i) for i in range(400)]
        self.assertEqual(50, len(selection(summaries)))
        self.assertEqual(50, len(selection(summaries)))
        self.assertEqual([], selection(summaries))
        self.assertEqual(100, selection.spent)

    def test_a_short_last_batch_is_trimmed_to_the_budget(self):
        selection = DeficitSelection(budget=70, batch_size=50)
        summaries = [summary(str(i), existing=5, seen=i) for i in range(400)]
        self.assertEqual(50, len(selection(summaries)))
        self.assertEqual(20, len(selection(summaries)))
        self.assertEqual([], selection(summaries))

    def test_no_duplicate_within_one_batch(self):
        selection = DeficitSelection(batch_size=10)
        summaries = [summary('a', existing=1, seen=50), summary('b', existing=1, seen=40)]
        self.assertEqual(['a', 'b'], names(selection(summaries)))

    def test_being_served_pushes_a_case_down_the_ranking(self):
        # What this run produced counts towards the pool, so one case cannot hog the budget.
        selection = DeficitSelection(batch_size=1)
        worn = summary('worn', existing=1, seen=9)        # 9.0
        other = summary('other', existing=1, seen=4)      # 4.0
        self.assertEqual(['worn'], names(selection([worn, other])))
        worn.successes.extend([object()] * 2)             # now 9/3 = 3.0
        self.assertEqual(['other'], names(selection([worn, other])))

    def test_ties_are_broken_at_random(self):
        # Otherwise the flat tail would be the same cases in the same order every run.
        seen_orders = set()
        for _ in range(50):
            selection = DeficitSelection(batch_size=2)
            summaries = [summary('a', existing=1, seen=6), summary('b', existing=1, seen=6)]
            seen_orders.add(tuple(names(selection(summaries))))
        self.assertEqual({('a', 'b'), ('b', 'a')}, seen_orders)

    def test_an_uncovered_case_ranks_last(self):
        # It has nothing to be repetitive with; NewEntitiesSelection is its run.
        selection = DeficitSelection(batch_size=1)
        summaries = [summary('uncovered', existing=0, seen=0), summary('any', existing=10, seen=1)]
        self.assertEqual(['any'], names(selection(summaries)))

    def test_a_case_that_failed_too_often_is_dropped(self):
        # It stays top-ranked because it never produced anything, so without this it
        # would take a slot in every batch for the rest of the run.
        selection = DeficitSelection(batch_size=1, max_errors=2)
        failing = summary('failing', existing=1, seen=99, errors=2)
        self.assertEqual(['other'], names(selection([failing, summary('other', existing=1, seen=2)])))

    def test_attempts_are_counted_for_the_report(self):
        selection = DeficitSelection(batch_size=1)
        worn = summary('worn', existing=1, seen=99)
        selection([worn])
        selection([worn])
        self.assertEqual([2], list(selection.processed.values()))

    def test_it_names_its_run_folder(self):
        self.assertEqual('deficit', DeficitSelection().name)
        self.assertEqual('new_entities', NewEntitiesSelection().name)


if __name__ == '__main__':
    unittest.main()
