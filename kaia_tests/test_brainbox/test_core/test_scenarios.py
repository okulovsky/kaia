
from kaia.brainbox import BrainBoxTask, BrainBoxTestApi
from kaia.brainbox.core import FailedJobArgument
from unittest import TestCase
from pprint import pprint

import time
from kaia.brainbox import IDecider

class WaitingDecider(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, arg = None):
        if arg is None:
            return 'OK'
        return f"OK-{arg}"


class ErroneousDecider(IDecider):
    def __init__(self, raise_in_call = True, raise_in_warm_up = False):
        self.raise_in_call = raise_in_call
        self.raise_in_warm_up = raise_in_warm_up

    def warmup(self, parameters: str):
        if self.raise_in_warm_up:
            raise ValueError("Error")

    def cooldown(self, parameters: str):
        pass

    def __call__(self):
        if self.raise_in_call:
            raise ValueError("Error")


class CollectingDecider(IDecider):
    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

    def __call__(self, **args):
        return dict(collected=True, arg=args)




services = dict(
    a=WaitingDecider(),
    b=WaitingDecider(),
    err = ErroneousDecider(True, False),
    collect=CollectingDecider(),
    err_warm = ErroneousDecider(False, True)
)

class ServiceTestCase(TestCase):
    def test_simple(self):
        tasks = [BrainBoxTask(
            id=f'{decider}-{i}',
            decider = decider,
            arguments = {},
        ) for i in range(3) for decider in ['b','a']]
        tasks, logs = BrainBoxTestApi.execute_serverless(tasks,services)
        self.assertListEqual([True]*6, [t.success for t in tasks])
        self.assertListEqual(['OK']*6, [t.result for t in tasks])


    def test_dependent(self):
        tasks = [
            BrainBoxTask(id='src',
                        decider='a',
                        arguments=dict(arg='X'),
                        ),
            BrainBoxTask(id='col',
                        decider='collect',
                        arguments=dict(),
                        dependencies = dict(arg='src')
                        ),
        ]
        tasks, log = BrainBoxTestApi.execute_serverless(tasks, services)
        self.assertEqual('OK-X', tasks[0].result)
        self.assertDictEqual(
            {'arg': {'arg': 'OK-X'}, 'collected': True},
            tasks[1].result
        )

    def test_dependent_list(self):
        tasks = [
            BrainBoxTask(id='src-x',
                        decider='a',
                        arguments=dict(arg='X'),
                        ),
            BrainBoxTask(id='src-y',
                        decider='a',
                        arguments=dict(arg='Y'),
                        ),
            BrainBoxTask(id='col',
                        decider='collect',
                        arguments=dict(),
                        dependencies={'x': 'src-x', 'y': 'src-y'}
                        ),
        ]
        tasks, log = BrainBoxTestApi.execute_serverless(tasks,services)
        self.assertDictEqual(
            {'collected': True, 'arg': {'x': 'OK-X', 'y': 'OK-Y'}},
            tasks[2].result
        )

    def test_parameters(self):
        tasks = []
        for i in range(3):
            for parameter in ['1','2','3']:
                tasks.append(BrainBoxTask(
                    id=f'src-{i}-{parameter}',
                    decider='a',
                    decider_parameters=parameter,
                    arguments=dict(arg='X'),
                ))
        tasks, log = BrainBoxTestApi.execute_serverless(tasks,services)
        is_warm_up = [l for l in log if l.event=='Warming up']
        self.assertEqual(3, len(is_warm_up))


    def test_error_handling(self):
        tasks = [
            BrainBoxTask(id='src-x',
                        decider='a',
                        arguments=dict(arg='X'),
                        ),
            BrainBoxTask(id='src-y',
                        decider='err',
                         arguments={}
                        ),
            BrainBoxTask(id='col',
                        decider='collect',
                        arguments=dict(),
                        dependencies={'x': 'src-x', 'y': 'src-y'}
                        ),
        ]
        tasks, log = BrainBoxTestApi.execute_serverless(tasks, services)
        print(tasks[-1].__dict__)
        self.assertTrue(tasks[2].success)
        self.assertFalse(tasks[1].success)
        self.assertTrue(tasks[0].success)
        self.assertEqual('OK-X', tasks[2].result['arg']['x'])
        self.assertIsInstance(tasks[2].result['arg']['y'], FailedJobArgument)


    def test_error_at_warmup(self):
        tasks = [
            BrainBoxTask(id='src-x', decider='err_warm', arguments=dict()),
            BrainBoxTask(id='src-y', decider='err_warm', arguments=dict()),
        ]
        tasks, log = BrainBoxTestApi.execute_serverless(tasks, services)
        for task in tasks:
            self.assertFalse(task.success)
            self.assertIsNotNone(task.error)

