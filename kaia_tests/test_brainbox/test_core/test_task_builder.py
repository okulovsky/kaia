from typing import Iterable
from kaia.brainbox import BrainBoxTask, BrainBoxTestApi
from unittest import TestCase
import inspect
from kaia.brainbox import IDecider
from dataclasses import dataclass, field

class Test(IDecider):
    def method(self, required_1, required_2, optional_1 = None, optional_2 = 'b', **kwargs):
        pass

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass


class TaskBuilderTestCase(TestCase):

    def test_task_builder(self):
        task = BrainBoxTask.call(Test).method(required_1=4,required_2=5).to_task()
        self.assertEqual('Test', task.decider)
        self.assertEqual('method', task.decider_method)
        self.assertDictEqual(dict(required_1=4, required_2=5), task.arguments)

    def test_task_builder_validates_parameters(self):
        self.assertRaises(Exception, lambda: BrainBoxTask.call(Test).method(x=4).to_task())

    def test_task_builder_with_args(self):
        task = BrainBoxTask.call(Test).method(2, 3).to_task()
        self.assertDictEqual(
            dict(required_1=2, required_2=3),
            task.arguments
        )

        task = BrainBoxTask.call(Test).method(2, 3, 4).to_task()
        self.assertDictEqual(
            dict(required_1=2, required_2=3, optional_1=4),
            task.arguments
        )

        task = BrainBoxTask.call(Test).method(2, required_2=3, optional_1=4).to_task()
        self.assertDictEqual(
            dict(required_1=2, required_2=3, optional_1=4),
            task.arguments
        )

        self.assertRaises(
            Exception,
            lambda: BrainBoxTask.call(Test).method(4).to_task()
        )

        self.assertRaises(
            Exception,
            lambda: BrainBoxTask.call(Test).method(2,3,required_1=4).to_task()
        )


