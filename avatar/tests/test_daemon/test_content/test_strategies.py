from dataclasses import dataclass
from unittest import TestCase
from avatar.daemon.common.content import (
    Feedback, IRecord,
    NewContentStrategy, GoodContentStrategy, AnyContentStrategy, SequentialStrategy, WeightedStrategy,
)


@dataclass
class Record(IRecord):
    file_id: str

    def get_id(self) -> str:
        return self.file_id

    def get_tags(self) -> dict:
        return {}


RECORDS = [Record('a'), Record('b'), Record('c')]


class StrategiesTestCase(TestCase):
    def test_new_content_prefers_the_unseen(self):
        feedback = Feedback({'a': {'seen': 2}, 'b': {'seen': 1}})
        self.assertEqual('c', NewContentStrategy(False).choose(RECORDS, feedback).get_id())

    def test_new_content_skips_the_bad(self):
        feedback = Feedback({'a': {'bad': 1}, 'b': {'seen': 1}})
        self.assertEqual('c', NewContentStrategy(False).choose(RECORDS, feedback).get_id())

    def test_new_content_returns_none_when_everything_is_bad(self):
        feedback = Feedback({r.file_id: {'bad': 1} for r in RECORDS})
        self.assertIsNone(NewContentStrategy(False).choose(RECORDS, feedback))

    def test_good_content_needs_a_seen_record(self):
        self.assertIsNone(GoodContentStrategy().choose(RECORDS, Feedback()))
        chosen = GoodContentStrategy().choose(RECORDS, Feedback({'b': {'seen': 1}}))
        self.assertEqual('b', chosen.get_id())

    def test_any_content_returns_none_on_empty(self):
        self.assertIsNone(AnyContentStrategy().choose([], Feedback()))
        self.assertIn(AnyContentStrategy().choose(RECORDS, Feedback()).get_id(), {'a', 'b', 'c'})

    def test_sequential_falls_through(self):
        feedback = Feedback({r.file_id: {'bad': 1} for r in RECORDS})
        strategy = SequentialStrategy(NewContentStrategy(False), AnyContentStrategy())
        self.assertIn(strategy.choose(RECORDS, feedback).get_id(), {'a', 'b', 'c'})

    def test_weighted_uses_the_only_weighted_strategy(self):
        strategy = WeightedStrategy(
            WeightedStrategy.Item(NewContentStrategy(False), 1.0),
            WeightedStrategy.Item(AnyContentStrategy(), 0.0),
        )
        self.assertEqual('a', strategy.choose(RECORDS, Feedback()).get_id())
