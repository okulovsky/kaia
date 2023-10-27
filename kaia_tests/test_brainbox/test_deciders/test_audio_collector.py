from unittest import TestCase

import jsonpickle
import pandas as pd

from kaia.brainbox.core import IDecider, BrainBoxTask
from kaia.brainbox.core.testing import run_service
from kaia.persona.dub.core import CutSpec, DubbingFragment
from kaia.brainbox.deciders.tortoise_tts import DubCollector, FakeDubDecider, FakeDubCollectorProcessor

import json





class DubCollectorTestCase(TestCase):
    def test_dub_collector(self):
        Sentence1 = 'start first timer'
        #            01234567890123456
        Sentence2 = 'cancel the timer'
        #            0123456789012345

        spec = {
            'id_1': [
                CutSpec(0, 6, DubbingFragment('Test1', 'start', False)),
                CutSpec(12, 5, DubbingFragment('Test1', 'timer', False)),
            ],
            'id_2': [
                CutSpec(0, 16, DubbingFragment('Test2', 'cancel the timer', False))
            ]
        }

        tasks = [
            BrainBoxTask(
                id='test-1',
                decider='dub',
                method='dub',
                arguments=dict(voice='test', text=Sentence1),
            ),
            BrainBoxTask(
                id='test-2',
                decider='dub',
                method='dub',
                arguments=dict(voice='test', text=Sentence2)
            ),
            BrainBoxTask(
                id='collect',
                decider='collect',
                method='collect',
                arguments=dict(spec=spec),
                dependencies=dict(
                    id_1 = 'test-1',
                    id_2 = 'test-2'
                )
            )
        ]
        jobs, _ = run_service(
            tasks,
            dict(dub=FakeDubDecider(), collect=DubCollector(FakeDubCollectorProcessor()))
        )
        result = jsonpickle.loads(json.dumps(jobs[-1].result))
        if len(result['errors'])!=0:
            print(result['errors'])
        self.assertEqual(0, len(result['errors']))
        result = result['records']
        for r in result:
            self.assertIsInstance(r, DubbingFragment)

        df = pd.DataFrame([r.__dict__ for r in result])
        pd.options.display.width = None
        self.assertListEqual(
            ['start ', 'START ', 'timer', 'TIMER', 'cancel the timer', 'CANCEL THE TIMER'],
            list(df.file_name)
        )



