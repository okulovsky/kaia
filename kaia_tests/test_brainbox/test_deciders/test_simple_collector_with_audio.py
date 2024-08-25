from unittest import TestCase

import pandas as pd

from kaia.brainbox import BrainBoxTask, BrainBoxTestApi, IDecider
from kaia.brainbox.deciders.fake_dub_decider import FakeDubDecider
from kaia.brainbox.deciders.collector import Collector
from kaia.brainbox import MediaLibrary
from kaia.infra import Loc
from pprint import pprint

import json

class ErroneousDecider(IDecider):
    def warmup(self, parameters: str):
        pass
    def cooldown(self, parameters: str):
        pass
    def __call__(self):
        raise ValueError()



class DubCollectorTestCase(TestCase):
    def test_dub_collector(self):
        Sentence1 = 'start first timer'
        Sentence2 = 'cancel the timer'

        tasks = [
            BrainBoxTask(
                id='test-1',
                decider='dub',
                arguments=dict(voice='test', text=Sentence1),
            ),
            BrainBoxTask(
                id='test-2',
                decider='dub',
                arguments=dict(voice='test', text=Sentence2)
            ),
            BrainBoxTask(
                id='test-3',
                decider='err',
                arguments={}
            ),
            BrainBoxTask(
                id='collect',
                decider=Collector.to_media_library,
                arguments=dict(tags=dict(id_1=dict(tag='a'), id_2=dict(tag='b'), id_3=dict(tag='c'))),
                dependencies=dict(
                    id_1 = 'test-1',
                    id_2 = 'test-2',
                    id_3 = 'test-3'
                )
            )
        ]

        with Loc.create_temp_folder('tests/dub_collector') as path:
            jobs, _ = BrainBoxTestApi.execute_serverless(
                tasks,
                dict(dub=FakeDubDecider(2), Collector=Collector(), err=ErroneousDecider()),
                path
            )

            if jobs[-1].error is not None:
                print(jobs[-1].error)
            self.assertIsNone(jobs[-1].error)
            result = jobs[-1].result

            result = MediaLibrary.read(path/result)

            self.assertEqual(1, len(result.errors))

            df = pd.DataFrame([json.loads(r.get_content()) for r in result.records])
            self.assertDictEqual(
                {'voice': {0: 'test', 1: 'test', 2: 'test', 3: 'test'},
                 'text': {0: 'start first timer', 1: 'start first timer', 2: 'cancel the timer', 3: 'cancel the timer'},
                 'option_index': {0: 0, 1: 1, 2: 0, 3: 1}
                 },
                df.to_dict()
            )

            df1 = pd.DataFrame([r.tags for r in result.records])
            self.assertDictEqual(
                {'tag': {0: 'a', 1: 'a', 2: 'b', 3: 'b'}, 'option_index': {0: 0, 1: 1, 2: 0, 3: 1}},
                df1.to_dict()
            )



