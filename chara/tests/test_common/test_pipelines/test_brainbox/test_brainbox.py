from brainbox import BrainBox
from brainbox.deciders import Mock, Ollama, Collector
from chara.common import BrainBoxUnit, BrainBoxCache, BrainBoxMerger, CharaApis
from unittest import TestCase
from foundation_kaia.misc import Loc




class MyMock(Mock):
    def __init__(self):
        super().__init__('Ollama')

    def question(self, prompt: str):
        if prompt == 'error':
            raise ValueError()
        return f'{prompt}1;{prompt}2'


def create_task(s: str):
    return BrainBox.Task.call(Ollama,'test-model').question(s)

class BrainBoxUnitTestCase(TestCase):
    def test_simple(self):
        with Loc.create_test_folder() as folder:
            cache = BrainBoxCache().initialize(folder)
            unit = BrainBoxUnit(
                create_task
            )
            with BrainBox.Api.Test([MyMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                unit.run(cache, ['a', 'error'])

            self.assertTrue(cache.ready)
            result = cache.read_result().to_list()
            self.assertEqual(2, len(result))
            self.assertEqual('a', result[0].case)
            self.assertEqual(1, len(result[0].options))
            R = 'a1;a2'
            self.assertEqual(R, result[0].brainbox_result)
            self.assertEqual(R, result[0].options[0].brainbox_option)
            self.assertEqual(R, result[0].options[0].option)

            self.assertEqual('error', result[1].case)
            self.assertIsNotNone(result[1].brainbox_error)
            self.assertIsNone(result[1].brainbox_result)

            result = cache.read_options().to_list()
            self.assertEqual([R], result)

            result = cache.read_cases_and_options().to_list()
            self.assertEqual([('a', R)], result)

            result = cache.read_cases_and_single_options().to_list()
            self.assertEqual([('a', R)], result)



    def test_with_divider(self):

        def _merge(case, option):
            if option=='b2':
                raise ValueError()
            return 'merged '+option

        def _divide(result):
            if 'c' in result:
                raise ValueError()
            return result.split(';')

        with Loc.create_test_folder() as folder:
            cache = BrainBoxCache().initialize(folder)
            unit = BrainBoxUnit(
                create_task,
                _merge,
                _divide
            )
            with BrainBox.Api.Test([MyMock(), Collector()]) as api:
                CharaApis.brainbox_api = api
                unit.run(cache, ['a', 'b', 'c', 'error'])

            self.assertTrue(cache.ready)
            result = cache.read_result().to_list()
            self.assertEqual('merged a1', result[0].options[0].option)
            self.assertEqual('merged a2', result[0].options[1].option)
            self.assertIsNone(result[0].brainbox_error)
            self.assertIsNone(result[0].divider_error)
            self.assertIsNone(result[0].options[0].merge_error)
            self.assertIsNone(result[0].options[1].merge_error)

            self.assertEqual('merged b1', result[1].options[0].option)
            self.assertIsNotNone(result[1].options[1].merge_error)

            self.assertIsNotNone(result[2].divider_error)

            self.assertIsNotNone(result[3].brainbox_error)


