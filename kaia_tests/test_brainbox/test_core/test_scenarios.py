
from kaia.brainbox.core import BrainBoxTask
from unittest import TestCase
from datetime import datetime

from kaia.brainbox.core.testing import WaitingDecider, CollectingDecider, run_service

services = dict(
    a=WaitingDecider(0, 0, 0, ),
    b=WaitingDecider(0, 0, 0, ),
    collect=CollectingDecider()
)

class ServiceTestCase(TestCase):
    def test_simple(self):
        tasks = [BrainBoxTask(
            id=f'{decider}-{i}',
            decider = decider,
            method='run',
            arguments = {},
        ) for i in range(3) for decider in ['b','a']]
        tasks, log = run_service(tasks,services)
        self.assertEqual([True]*6, [t.success for t in tasks])


    def test_dependent(self):
        tasks = [
            BrainBoxTask(id='src',
                        decider='a',
                        method='run',
                        arguments=dict(arg='X'),
                        ),
            BrainBoxTask(id='col',
                        decider='collect',
                        method='run',
                        arguments=dict(),
                        dependencies = dict(arg='src')
                        ),
        ]
        tasks, log = run_service(tasks, services)
        self.assertEqual('OK-X', tasks[0].result)
        self.assertDictEqual(
            {'arg': {'arg': 'OK-X'}, 'collected': True},
            tasks[1].result
        )

    def test_dependent_list(self):
        tasks = [
            BrainBoxTask(id='src-x',
                        decider='a',
                        method='run',
                        arguments=dict(arg='X'),
                        ),
            BrainBoxTask(id='src-y',
                        decider='a',
                        method='run',
                        arguments=dict(arg='Y'),
                        ),
            BrainBoxTask(id='col',
                        decider='collect',
                        method='run',
                        arguments=dict(),
                        dependencies={'x': 'src-x', 'y': 'src-y'}
                        ),
        ]
        tasks, log = run_service(tasks,services)
        self.assertDictEqual(
            {'collected': True, 'arg': {'x': 'OK-X', 'y': 'OK-Y'}},
            tasks[2].result
        )










