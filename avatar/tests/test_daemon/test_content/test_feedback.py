from dataclasses import dataclass
from unittest import TestCase
from foundation_kaia.misc import Loc
from avatar.daemon.common.content import Feedback, FileFeedbackStorage, InMemoryFeedbackStorage


class FeedbackTestCase(TestCase):
    def test_unknown_id_is_empty(self):
        feedback = Feedback({'a': {'seen': 1}})
        self.assertEqual({}, dict(feedback['b']))
        self.assertEqual(0, feedback.get('b', 'seen'))

    def test_feedback_is_not_mutable(self):
        feedback = Feedback({'a': {'seen': 1}})
        with self.assertRaises(TypeError):
            feedback['a']['seen'] = 5

    def test_source_dict_is_copied(self):
        data = {'a': {'seen': 1}}
        feedback = Feedback(data)
        data['a']['seen'] = 5
        self.assertEqual(1, feedback.get('a', 'seen'))

    def test_append_returns_a_new_value_and_leaves_the_old_one(self):
        storage = InMemoryFeedbackStorage()
        before = storage.load()
        after = storage.append('a', {'seen': 1})
        self.assertEqual(0, before.get('a', 'seen'))
        self.assertEqual(1, after.get('a', 'seen'))

    def test_append_accumulates(self):
        storage = InMemoryFeedbackStorage()
        storage.append('a', {'seen': 1})
        storage.append('a', {'seen': 1, 'good': 1})
        self.assertEqual({'seen': 2, 'good': 1}, dict(storage.load()['a']))

    def test_two_storages_over_one_file_agree(self):
        with Loc.create_test_folder() as folder:
            first = FileFeedbackStorage(folder/'feedback.json')
            second = FileFeedbackStorage(folder/'feedback.json')
            self.assertEqual(0, second.load().get('a', 'seen'))
            first.append('a', {'seen': 1})
            self.assertEqual(1, second.load().get('a', 'seen'))

    def test_missing_file_is_empty(self):
        with Loc.create_test_folder() as folder:
            self.assertEqual(0, len(FileFeedbackStorage(folder/'nope.json').load()))
