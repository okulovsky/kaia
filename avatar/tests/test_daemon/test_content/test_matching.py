from dataclasses import dataclass
from unittest import TestCase
from avatar.daemon.common.content import ContentFinder, Feedback, IRecord, InMemoryFeedbackStorage


@dataclass
class Record(IRecord):
    content: str
    tag_1: str
    tag_2: str
    tag_3: str
    filename: str

    def get_id(self) -> str:
        return self.filename

    def get_tags(self) -> dict:
        return {key: value for key, value in self.__dict__.items() if key != 'filename'}


def records():
    return [
        Record(f'{a}{b}{c}', str(a), str(b), str(c), f'{a}{b}{c}')
        for a in range(3) for b in range(3) for c in range(3)
    ]


class MatchingTestCase(TestCase):
    def test_matching_feedback(self):
        finder = ContentFinder()
        storage = InMemoryFeedbackStorage()
        result = finder.find(records(), storage.load(), strong=dict(tag_1='1'))
        self.assertEqual('100', result.content)
        storage.append(result.get_id(), {'seen': 1})
        result = finder.find(records(), storage.load(), strong=dict(tag_1='1'))
        self.assertEqual('101', result.content)

    def test_matching_strong(self):
        result = ContentFinder().find(records(), Feedback(), strong=dict(tag_1='1', tag_2='2'))
        self.assertEqual('120', result.content)

    def test_matching_weak(self):
        result = ContentFinder().find(records(), Feedback(), weak=dict(tag_1='1', tag_2='2'))
        self.assertEqual('120', result.content)

    def test_matching_strong_missing(self):
        result = ContentFinder().find(records(), Feedback(), strong=dict(new_tag='1'))
        self.assertIsNone(result)

    def test_matching_weak_missing(self):
        result = ContentFinder().find(records(), Feedback(), weak=dict(new_tag='1'))
        self.assertEqual('000', result.content)

    def test_matching_weak_missing_partial(self):
        result = ContentFinder().find(records(), Feedback(), weak=dict(tag_1='1', new_tag='1'))
        self.assertEqual('100', result.content)

    def test_matching_weak_and_strong(self):
        result = ContentFinder().find(
            records(), Feedback(),
            strong=dict(tag_1='1'),
            weak=dict(tag_2='2', new_tag='3'),
        )
        self.assertEqual('120', result.content)
