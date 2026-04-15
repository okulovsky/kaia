from unittest import TestCase
from brainbox.framework.common import ISelfManagingDecider
from brainbox.framework.brainbox import BrainBox
from brainbox.framework.task.task_builder import Dependency
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.job_processing import FailedJobArgument
from brainbox.framework.app.serverless_test import ServerlessTest


class WaitingDecider(ISelfManagingDecider):
    def run(self, arg=None):
        if arg is None:
            return 'OK'
        return f"OK-{arg}"


class WaitingDecider2(WaitingDecider):
    pass


class ErroneousDecider(ISelfManagingDecider):
    def run(self):
        raise ValueError("Error")


class CollectingDecider(ISelfManagingDecider):
    def run(self, x=None, y=None):
        return dict(collected=True, arg=dict(x=x, y=y))


class WarmupErroneousDecider(ISelfManagingDecider):
    def run(self):
        return "OK"

    def warmup(self, parameter: str | None):
        raise ValueError()


services = [
    WaitingDecider(),
    WaitingDecider2(),
    ErroneousDecider(),
    CollectingDecider(),
    WarmupErroneousDecider(),
]


class TestSimple(TestCase):
    def test_simple(self):
        with ServerlessTest(registry=ControllerRegistry(services)) as api:
            tasks = [
                BrainBox.TaskBuilder.call(decider, id=f'{decider.__name__}-{i}').run()
                for i in range(3) for decider in [WaitingDecider, WaitingDecider2]
            ]
            ids = api.add(tasks)
            result = api.join(ids)

            self.assertListEqual([True] * 6, [api.tasks.get_job(id).success for id in ids])
            self.assertListEqual(['OK'] * 6, result)


class TestDependencies(TestCase):
    def test_dependent(self):
        with ServerlessTest(registry=ControllerRegistry(services)) as api:
            task1 = BrainBox.TaskBuilder.call(WaitingDecider, id='src').run('X')
            task2 = BrainBox.TaskBuilder.call(CollectingDecider, id='col').run(x=Dependency('src'))
            results = api.execute([task1, task2])
            self.assertEqual('OK-X', results[0])
            self.assertDictEqual(
                {'arg': {'x': 'OK-X', 'y': None}, 'collected': True},
                results[1]
            )

    def test_dependent_list(self):
        with ServerlessTest(registry=ControllerRegistry(services)) as api:
            task_1 = BrainBox.TaskBuilder.call(WaitingDecider, id='src-x').run('X')
            task_2 = BrainBox.TaskBuilder.call(WaitingDecider, id='src-y').run('Y')
            task_3 = BrainBox.TaskBuilder.call(CollectingDecider, id='col').run(
                x=Dependency('src-x'), y=Dependency('src-y')
            )
            results = api.execute([task_1, task_2, task_3])
            self.assertDictEqual(
                {'collected': True, 'arg': {'x': 'OK-X', 'y': 'OK-Y'}},
                results[2]
            )


class TestParameters(TestCase):
    def test_parameters_cause_separate_warmups(self):
        with ServerlessTest(registry=ControllerRegistry(services)) as api:
            tasks = []
            for i in range(3):
                for parameter in ['1', '2', '3']:
                    tasks.append(
                        BrainBox.TaskBuilder.call(WaitingDecider, id=f'src-{i}-{parameter}', parameter=parameter).run('X')
                    )
            api.execute(tasks)


class TestErrorHandling(TestCase):
    def test_error_propagates_as_failed_job_argument(self):
        with ServerlessTest(registry=ControllerRegistry(services)) as api:
            tasks = [
                BrainBox.TaskBuilder.call(WaitingDecider, id='src-x').run('X'),
                BrainBox.TaskBuilder.call(ErroneousDecider, id='src-y').run(),
                BrainBox.TaskBuilder.call(CollectingDecider, id='col').run(
                    x=Dependency('src-x'), y=Dependency('src-y')
                ),
            ]
            ids = api.add(tasks)
            api.tasks.base_join(ids, ignore_errors=True)
            jobs = [api.tasks.get_job(id) for id in ids]

            self.assertTrue(jobs[0].success)
            self.assertFalse(jobs[1].success)
            self.assertTrue(jobs[2].success)
            self.assertEqual('OK-X', jobs[2].result['arg']['x'])
            self.assertIsInstance(jobs[2].result['arg']['y'], FailedJobArgument)

    def test_error_at_warmup(self):
        with ServerlessTest(registry=ControllerRegistry(services)) as api:
            tasks = [
                BrainBox.TaskBuilder.call(WarmupErroneousDecider, id='src-x').run(),
                BrainBox.TaskBuilder.call(WarmupErroneousDecider, id='src-y').run(),
            ]
            ids = api.add(tasks)
            api.tasks.base_join(ids, ignore_errors=True)
            jobs = [api.tasks.get_job(id) for id in ids]
            for job in jobs:
                self.assertFalse(job.success)
                self.assertIsNotNone(job.error)


class TestResultRetrieval(TestCase):
    def test_result_endpoint(self):
        with ServerlessTest(registry=ControllerRegistry(services)) as api:
            task = BrainBox.TaskBuilder.call(WaitingDecider, id='test').run()
            self.assertEqual('OK', api.execute(task))
            self.assertEqual('OK', api.tasks.get_result('test'))


class CustomClass:
    def __init__(self, value):
        self.value = value


class CustomDecider(ISelfManagingDecider):
    def run(self, arg):
        return CustomClass(arg)

    def run_simple(self, arg):
        return f'OK-{arg}'


class TestCustomClassRoundTrip(TestCase):
    """Custom (non-dataclass) objects survive the pickle round-trip through the DB"""

    def test_custom_class_as_argument_and_result(self):
        with ServerlessTest(registry=ControllerRegistry([CustomDecider()])) as api:
            results = api.execute([
                BrainBox.TaskBuilder.call(CustomDecider).run_simple('X'),
                BrainBox.TaskBuilder.call(CustomDecider).run('X'),
                BrainBox.TaskBuilder.call(CustomDecider, id='t3').run(CustomClass('X')),
                BrainBox.TaskBuilder.call(CustomDecider).run(Dependency('t3')),
            ])

            self.assertEqual('OK-X', results[0])

            self.assertIsInstance(results[1], CustomClass)
            self.assertEqual('X', results[1].value)

            self.assertIsInstance(results[2], CustomClass)
            self.assertIsInstance(results[2].value, CustomClass)
            self.assertEqual('X', results[2].value.value)

            self.assertIsInstance(results[3], CustomClass)
            self.assertIsInstance(results[3].value, CustomClass)
            self.assertIsInstance(results[3].value.value, CustomClass)
            self.assertEqual('X', results[3].value.value.value)
