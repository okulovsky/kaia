from unittest import TestCase
from kaia.brainbox import IDecider, BrainBoxTask, BrainBoxTestApi
from pprint import pprint

class CustomClass:
    def __init__(self, value):
        self.value = value

class TestDecider(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def run(self, arg):
        return CustomClass(arg)

    def run_simple(self, arg):
        return f'OK-{arg}'

class BrainBoxWebServerEmptyTestCase(TestCase):
    def test_all_kinds_of_data(self):
        with BrainBoxTestApi(dict(test=TestDecider())) as api:
            results = api.execute([
                    BrainBoxTask(id = 'test-1',decider = 'test', decider_method='run_simple',arguments=dict(arg='X')),
                    BrainBoxTask(id = 'test-2', decider = 'test', decider_method='run', arguments=dict(arg='X')),
                    BrainBoxTask(id = 'test-3', decider = 'test', decider_method='run', arguments=dict(arg = CustomClass('X'))),
                    BrainBoxTask(id='test-4', decider='test', decider_method='run',arguments=dict(), dependencies=dict(arg='test-3'))
                ])


            self.assertEqual('OK-X', results[0])

            r = results[1]
            self.assertIsInstance(r, CustomClass)
            self.assertEqual(r.value, 'X')

            r = results[2]
            self.assertIsInstance(r, CustomClass)
            self.assertIsInstance(r.value, CustomClass)
            self.assertEqual(r.value.value, 'X')

            r = results[3]
            self.assertIsInstance(r, CustomClass)
            self.assertIsInstance(r.value, CustomClass)
            self.assertIsInstance(r.value.value, CustomClass)
            self.assertEqual(r.value.value.value, 'X')





