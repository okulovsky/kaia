from datetime import datetime
from unittest import TestCase
from chara.common import Chara
from foundation_kaia.misc import Loc


def _run(root, value):
    folder = Chara.start_or_resume(root, '$')
    Chara.call(lambda: value, 'step')()
    return folder


class StartOrResumeTestCase(TestCase):
    def test_creates_folder_when_root_is_empty(self):
        with Loc.create_test_folder() as root:
            folder = _run(root, 1)
            self.assertEqual(root, folder.parent)
            self.assertTrue(folder.name.startswith('$'))

    def test_finished_run_starts_a_new_one(self):
        with Loc.create_test_folder() as root:
            first = _run(root, 1)
            second = _run(root, 2)
            self.assertNotEqual(first, second)
            self.assertEqual(2, Chara.from_folder(second).result)

    def test_unfinished_run_is_resumed(self):
        with Loc.create_test_folder() as root:
            unfinished = root / ('$' + datetime(2026, 1, 1).isoformat())
            unfinished.mkdir()
            self.assertEqual(unfinished, _run(root, 1))

    def test_prefix_is_used(self):
        with Loc.create_test_folder() as root:
            other = root / ('$' + datetime(2026, 1, 1).isoformat())
            other.mkdir()
            folder = Chara.start_or_resume(root, 'run_')
            Chara.call(lambda: 1, 'step')()
            self.assertNotEqual(other, folder)
            self.assertTrue(folder.name.startswith('run_'))

    def test_ignores_folders_not_named_by_timestamp(self):
        with Loc.create_test_folder() as root:
            (root / '$pipeline_2026-01-01').mkdir()
            (root / 'other').mkdir()
            first = _run(root, 1)
            second = _run(root, 2)
            self.assertNotEqual(first, second)
            self.assertNotIn(second.name, ('$pipeline_2026-01-01', 'other'))
