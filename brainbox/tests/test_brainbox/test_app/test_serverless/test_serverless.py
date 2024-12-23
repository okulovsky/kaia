from brainbox.framework import (
    BrainBoxTask, BrainBoxApi, FailedJobArgument, ControllerOverDecider,
    IDecider, ISelfManagingDecider
)
from unittest import TestCase

class WaitingDecider(IDecider):
    def __call__(self, arg = None):
        if arg is None:
            return 'OK'
        return f"OK-{arg}"


class ErroneousDecider(ISelfManagingDecider):
    def __init__(self, raise_in_call = True, raise_in_warm_up = False):
        self.raise_in_call = raise_in_call
        self.raise_in_warm_up = raise_in_warm_up

    def warmup(self, parameters: str):
        if self.raise_in_warm_up:
            raise ValueError("Error")

    def cooldown(self):
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


services = [
    ControllerOverDecider(WaitingDecider(), 'a'),
    ControllerOverDecider(WaitingDecider(), 'b'),
    ControllerOverDecider(ErroneousDecider(True, False), 'err'),
    ControllerOverDecider(CollectingDecider(), 'collect'),
    ControllerOverDecider(ErroneousDecider(False, True), 'err_warm')
]

class ServiceTestCase(TestCase):
    def test_simple(self):
        with BrainBoxApi.ServerlessTest(services) as api:
            tasks = [BrainBoxTask(
                id=f'{decider}-{i}',
                decider = decider,
                arguments = {},
                ) for i in range(3) for decider in ['b','a']]
            result = api.execute(tasks)
            self.assertListEqual([True]*6, [api.job(t.id).success for t in tasks])
            self.assertListEqual(['OK']*6, result)



    def test_dependent(self):
        with BrainBoxApi.ServerlessTest(services) as api:
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
            results = api.execute(tasks)
            self.assertEqual('OK-X', results[0])
            self.assertDictEqual(
                {'arg': {'arg': 'OK-X'}, 'collected': True},
                results[1]
            )

    def test_dependent_list(self):
        with BrainBoxApi.ServerlessTest(services) as api:
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
            results = api.execute(tasks)
            self.assertDictEqual(
                {'collected': True, 'arg': {'x': 'OK-X', 'y': 'OK-Y'}},
                results[2]
            )

    def test_parameters(self):
        with BrainBoxApi.ServerlessTest(services) as api:
            tasks = []
            for i in range(3):
                for parameter in ['1','2','3']:
                    tasks.append(BrainBoxTask(
                        id=f'src-{i}-{parameter}',
                        decider='a',
                        decider_parameter=parameter,
                        arguments=dict(arg='X'),
                    ))
            api.execute(tasks)
            log = api.get_operator_log()
            is_warm_up = [l for l in log if l.event=='Starting']
            self.assertEqual(3, len(is_warm_up))


    def test_error_handling(self):
        with BrainBoxApi.ServerlessTest(services) as api:
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
            api.add(tasks)
            ids = [t.id for t in tasks]
            api.base_join(ids, allow_failures=True)

            tasks = [api.job(id) for id in ids]

            self.assertTrue(tasks[2].success)
            self.assertFalse(tasks[1].success)
            self.assertTrue(tasks[0].success)
            self.assertEqual('OK-X', tasks[2].result['arg']['x'])
            self.assertIsInstance(tasks[2].result['arg']['y'], FailedJobArgument)


    def test_error_at_warmup(self):
        with BrainBoxApi.ServerlessTest(services) as api:
            tasks = [
                BrainBoxTask(id='src-x', decider='err_warm', arguments=dict()),
                BrainBoxTask(id='src-y', decider='err_warm', arguments=dict()),
            ]
            api.add(tasks)
            api.base_join([task.id for task in tasks], allow_failures=True)
            tasks = [api.job(task.id) for task in tasks]
            for task in tasks:
                self.assertFalse(task.success)
                self.assertIsNotNone(task.error)

