from unittest import TestCase
from brainbox.framework import IDecider, BrainBoxTask, BrainBoxApi, BrainBoxTaskPack
from pprint import pprint


class CustomClass:
    def __init__(self, value):
        self.value = value

class TestDecider(IDecider):
    def run(self, arg):
        return CustomClass(arg)

    def run_simple(self, arg):
        return f'OK-{arg}'


class BrainBoxWebServerEmptyTestCase(TestCase):
    def test_all_kinds_of_data(self):
        with BrainBoxApi.Test([TestDecider()]) as api:
            results = api.execute([
                    BrainBoxTask(id = 'test-1',decider = 'TestDecider', decider_method='run_simple',arguments=dict(arg='X')),
                    BrainBoxTask(id = 'test-2', decider = 'TestDecider', decider_method='run', arguments=dict(arg='X')),
                    BrainBoxTask(id = 'test-3', decider = 'TestDecider', decider_method='run', arguments=dict(arg = CustomClass('X'))),
                    BrainBoxTask(id='test-4', decider='TestDecider', decider_method='run',arguments=dict(), dependencies=dict(arg='test-3'))
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

    def test_builder_as_argument(self):
        with BrainBoxApi.Test([TestDecider()]) as api:
            r = api.execute(BrainBoxTask(decider='TestDecider', decider_method='run_simple', arguments=dict(arg='1')))
            self.assertEqual("OK-1", r)

            r = api.execute(BrainBoxTask(decider=TestDecider.run_simple, arguments=dict(arg='2')))
            self.assertEqual("OK-2", r)

            r = api.execute(BrainBoxTask.call(TestDecider).run_simple("3").to_task())
            self.assertEqual("OK-3", r)

            r = api.execute(BrainBoxTask.call(TestDecider).run_simple("4"))
            self.assertEqual("OK-4", r)

            pack = BrainBoxTaskPack(
                BrainBoxTask.call(TestDecider).run_simple('10'),
                (
                    BrainBoxTask.call(TestDecider).run_simple('11'),
                    BrainBoxTask.call(TestDecider).run_simple('12')
                )
            )
            result = api.execute(pack)
            self.assertEqual("OK-10", result)


