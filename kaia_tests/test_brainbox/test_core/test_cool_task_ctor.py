from typing import Iterable
from kaia.brainbox import BrainBoxTask, BrainBoxTestApi
from unittest import TestCase
import inspect
from kaia.brainbox import IDecider
from dataclasses import dataclass, field

class Test(IDecider):
    def method(self, a, b):
        return a+b

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass

class TestSignature(IDecider):
    def method(self, required_1, required_2, optional_1 = None, optional_2 = 'b', **kwargs):
        pass

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass




class CoolCtorTestCase(TestCase):
    def test_cool_ctor(self):
        services = dict(Test=Test())
        task = BrainBoxTask(id = BrainBoxTask.safe_id(), decider=Test, decider_method=Test.method, arguments=dict(a=5, b=6))
        result, _ = BrainBoxTestApi.execute_serverless([task], services)
        self.assertEqual(11, result[0].result)

    def test_cooler_ctor(self):
        services = dict(Test=Test())
        task = BrainBoxTask(decider=Test.method, arguments=dict(a=6, b=6))
        result, _ = BrainBoxTestApi.execute_serverless([task], services)
        self.assertEqual(12, result[0].result)

    def test_arguments_exceptions(self):
        self.assertRaises(
            Exception,
            lambda: BrainBoxTask(decider=TestSignature.method, arguments=dict(required_1=1))
        )

        self.assertRaises(
            Exception,
            lambda: BrainBoxTask(decider=TestSignature, decider_method=TestSignature.method, arguments=dict(required_1=1))
        )


    def test_task_builder(self):
        task = BrainBoxTask.call(Test).method(a=4,b=5).to_task()
        self.assertEqual('Test', task.decider)
        self.assertEqual('method', task.decider_method)
        self.assertDictEqual(dict(a=4, b=5), task.arguments)

    def test_task_builder_validates_parameters(self):
        self.assertRaises(Exception, lambda: BrainBoxTask.call(Test).method(x=4).to_task())








