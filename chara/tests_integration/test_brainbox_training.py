from brainbox import BrainBox
from brainbox.deciders import HelloBrainBox
from chara.common import CharaApis
from chara.common.pipelines.brainbox_training.brainbox_training_unit import BrainBoxTrainingCache
from foundation_kaia.misc import Loc
from unittest import TestCase


class HelloBrainBoxTrainingTestCase(TestCase):
    def test_training_success(self):
        with BrainBox.Api.Test() as api:
            CharaApis.brainbox_api = api
            with Loc.create_test_folder() as folder:
                cache = BrainBoxTrainingCache(folder / 'success')
                cache.pipeline(BrainBox.Task.call(HelloBrainBox).training(b'abcd'))
                result = cache.read_result()
                self.assertTrue(result.success)
                self.assertEqual('RESULT', result.result)
                self.assertGreater(len(result.log), 0)
                self.assertGreater(result.last_reported_progress, 0)

    def test_training_exception(self):
        with BrainBox.Api.Test() as api:
            CharaApis.brainbox_api = api
            with Loc.create_test_folder() as folder:
                cache = BrainBoxTrainingCache(folder / 'exception')
                cache.pipeline(BrainBox.Task.call(HelloBrainBox).training(b'abcd', raise_exception=True))
                result = cache.read_result()
                self.assertFalse(result.success)
                self.assertIsNotNone(result.error)
                self.assertIsNone(result.result)
                self.assertGreater(len(result.log), 0)
                self.assertGreater(result.last_reported_progress, 0)
