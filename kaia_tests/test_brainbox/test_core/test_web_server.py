from unittest import TestCase
from kaia.infra.app import KaiaApp
from kaia.infra.loc import Loc
from kaia.infra.comm import Sql
from kaia.brainbox.core import IDecider, BrainBoxTask
from kaia.brainbox.core.testing import WaitingDecider, run_web_server
from pprint import pprint

class CustomClass:
    def __init__(self, value):
        self.value = value

class TestDecider(IDecider):
    def warmup(self):
        pass

    def cooldown(self):
        pass

    def run(self, arg):
        return CustomClass(arg)

    def run_simple(self, arg):
        return f'OK-{arg}'

class BrainBoxWebServerEmptyTestCase(TestCase):
    def test_all_kinds_of_data(self):
        jobs, results = run_web_server(
            [
                BrainBoxTask('test-1','test','run_simple',dict(arg='X')),
                BrainBoxTask('test-2', 'test', 'run', dict(arg='X')),
                BrainBoxTask('test-3', 'test', 'run', dict(arg = CustomClass('X'))),
                BrainBoxTask('test-4', 'test', 'run', dict(), dependencies=dict(arg='test-3'))
            ],
            dict(test=TestDecider())
        )

        for r in [jobs[0].result, results[0]]:
            self.assertEqual('OK-X', r)

        for r in [jobs[1].result, results[1]]:
            self.assertIsInstance(r, CustomClass)
            self.assertEqual(r.value, 'X')

        for r in [jobs[2].result, results[2]]:
            self.assertIsInstance(r, CustomClass)
            self.assertIsInstance(r.value, CustomClass)
            self.assertEqual(r.value.value, 'X')

        for r in [jobs[3].result, results[3]]:
            self.assertIsInstance(r, CustomClass)
            self.assertIsInstance(r.value, CustomClass)
            self.assertIsInstance(r.value.value, CustomClass)
            self.assertEqual(r.value.value.value, 'X')



