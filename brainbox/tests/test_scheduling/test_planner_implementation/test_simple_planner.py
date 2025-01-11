from unittest import TestCase
from brainbox.framework.job_processing import (
    JobForPlanner, DeciderInstanceKey, PlannerArguments,
    OperatorStateForPlanner, StartCommand, StopCommand, AssignAction
)
from brainbox import SimplePlanner
from datetime import datetime


class Scene:
    def __init__(self):
        self._states = []
        self._tasks = []

    def state(self, decider: str, parameter: str|None = None):
        instance_id = str(len(self._states))
        self._states.append(OperatorStateForPlanner(
            instance_id,
            DeciderInstanceKey(decider, parameter),
            True,
            None
        ))
        return self

    def task(self, decider: str, parameter: str|None = None, assigned: bool = False, count: int = 1):
        for i in range(count):
            task = JobForPlanner(
                str(len(self._tasks)),
                decider,
                parameter,
                received_timestamp=datetime(2020, 1, 1 + len(self._tasks)),
                assigned=assigned,
                ordering_token=None,

            )
            self._tasks.append(task)
        return self

    def get_args(self):
        return PlannerArguments(
            tuple(self._tasks),
            tuple(self._states)
        )





class SimplePlannerTestCase(TestCase):
    def make_test(self, scene, zero: bool = False):
        args = scene.get_args()
        plan = SimplePlanner()
        result = plan.plan(args)
        if zero:
            self.assertEqual(0, len(result))
            return None
        self.assertEqual(1, len(result))
        return result[0]


    def test_up_alphabet(self):
        result = self.make_test(
            Scene()
            .task('b', count=2)
            .task('a', count=2)
        )
        self.assertIsInstance(result, StartCommand)
        self.assertEqual('a', result.key.decider_name)

    def test_up_count(self):
        result = self.make_test(
            Scene()
            .task('b', count=3)
            .task('a', count=2)
        )
        self.assertIsInstance(result, StartCommand)
        self.assertEqual('b', result.key.decider_name)

    def test_assign_earliest(self):
        result = self.make_test(
            Scene()
            .task('b', count=2)
            .task('a', count=2)
            .state('a')
        )
        self.assertIsInstance(result, AssignAction)
        self.assertEqual('2', result.job_id)

    def test_assign_second(self):
        result = self.make_test(
            Scene()
            .task('a', count=2)
            .task('a', assigned=True)
            .state('a')
        )
        self.assertIsInstance(result, AssignAction)
        self.assertEqual('0', result.job_id)

    def test_doesnt_assign_second(self):
        self.make_test(
            Scene()
            .task('a', count=2)
            .task('a', assigned=True, count=2)
            .state('a'),
            zero=True
        )


    def test_down(self):
        result = self.make_test(
            Scene()
            .task('b')
            .state('a')
        )
        self.assertIsInstance(result, StopCommand)
        self.assertEqual(result.instance_id, '0')


    def test_parameter_down(self):
        result = self.make_test(
            Scene()
            .task('a', 'param1')
            .state('a', 'param2')
        )
        self.assertIsInstance(result, StopCommand)
        self.assertEqual(result.instance_id, '0')

    def test_parameter_up(self):
        result = self.make_test(
            Scene()
            .task('a', 'param2')
            .task('a', 'param1')
        )
        self.assertIsInstance(result, StartCommand)
        self.assertEqual('param1', result.key.parameter)

    def test_parameter_assign(self):
        result = self.make_test(
            Scene()
            .task('a', 'param2')
            .task('a', 'param1')
            .state('a', 'param1')
        )
        self.assertIsInstance(result, AssignAction)
        self.assertEqual('1', result.job_id)










