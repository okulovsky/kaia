from kaia.brainbox import BrainBoxTestApi, IDecider, BrainBoxTask, BrainBoxTaskPack
from unittest import TestCase

class Test(IDecider):
    def test(self, a, b):
        return a+b

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

class BrainBoxApiTestCase(TestCase):
    def test_brainbox_api(self):
        with BrainBoxTestApi(dict(Test=Test())) as api:
            self.assertEqual(
                11,
                api.execute(BrainBoxTask(
                    decider='Test',
                    decider_method='test',
                    arguments=dict(a=5, b=6)
                )))

            self.assertEqual(
                12,
                api.execute(BrainBoxTask(
                    decider=Test.test,
                    arguments=dict(a=6, b=6)
                ))
            )

            self.assertEqual(
                13,
                api.execute(BrainBoxTask.call(Test).test(a=7, b=6).to_task())
            )

            self.assertEqual(
                14,
                api.execute(BrainBoxTask.call(Test).test(a=7,b=7))
            )