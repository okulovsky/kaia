from unittest import TestCase
from chara.common import Chara, brainbox_training_pipeline
from brainbox.deciders import HelloBrainBox
from brainbox import BrainBox
from foundation_kaia.misc import Loc

class BrainboxTrainingTest(TestCase):
    def test_training(self):
        with Loc.create_test_folder() as folder:
            Chara.start(folder)
            with BrainBox.Api.serverless_test() as api:
                Chara.Apis.brainbox_api = api
                task = HelloBrainBox.new_task().training(b'abcd')
                result = Chara.call(brainbox_training_pipeline)(task)
            self.assertEqual('RESULT', result)
