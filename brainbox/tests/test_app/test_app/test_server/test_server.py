from unittest import TestCase
from brainbox.framework.common import ISelfManagingDecider
from brainbox.framework.brainbox import BrainBox
from brainbox.framework.task.task_builder import Dependency
from brainbox.framework.app.api import BrainBoxApi


class CustomClass:
    def __init__(self, value):
        self.value = value


class CustomDecider(ISelfManagingDecider):
    def run(self, arg):
        return CustomClass(arg)

    def run_simple(self, arg):
        return f'OK-{arg}'


class TestCustomClassRoundTrip(TestCase):
    def test_custom_class_as_argument_and_result(self):
        with BrainBoxApi.test([CustomDecider()], port=18190) as api:
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
