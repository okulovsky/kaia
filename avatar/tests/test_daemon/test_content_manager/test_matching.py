from dataclasses import dataclass
from unittest import TestCase
from avatar.daemon.common.content_manager import DataClassDataProvider, ContentManager

@dataclass
class Record:
    content: str
    tag_1: str
    tag_2: str
    tag_3: str
    filename: str

def manager():
    return ContentManager[Record](DataClassDataProvider([
        Record(f'{a}{b}{c}', str(a), str(b), str(c), f'{a}{b}{c}')
        for a in range(3) for b in range(3) for c in range(3)
    ]))

class MatchingTestCase(TestCase):
    def test_matching_feedback(self):
        m = manager()
        result = m.match().strong(dict(tag_1='1')).find_content()
        self.assertEqual('100', result.content)
        m.feedback(result.filename, 'seen')
        result = m.match().strong(dict(tag_1='1')).find_content()
        self.assertEqual('101', result.content)

    def test_matching_strong(self):
        result = manager().match().strong(dict(tag_1='1', tag_2='2')).find_content()
        self.assertEqual('120', result.content)

    def test_matching_weak(self):
        result = manager().match().weak(dict(tag_1='1', tag_2='2')).find_content()
        self.assertEqual('120', result.content)

    def test_matching_strong_missing(self):
        result = manager().match().strong(dict(new_tag='1')).find_content()
        self.assertIsNone(result)

    def test_matching_weak_missing(self):
        result = manager().match().weak(dict(new_tag='1')).find_content()
        self.assertEqual('000', result.content)

    def test_matching_weak_missing_partial(self):
        result = manager().match().weak(dict(tag_1='1', new_tag='1')).find_content()
        self.assertEqual('100', result.content)

    def test_matching_weak_and_strong(self):
        result = manager().match().strong(dict(tag_1='1')).weak(dict(tag_2='2', new_tag='3')).find_content()
        self.assertEqual('120', result.content)
