from unittest import TestCase
from brainbox.deciders.utils.hello_brainbox.api import HelloBrainBox
from brainbox.framework import BrainBoxTask, Dependency


class TaskBuilderTestCase(TestCase):
    def test_plain_arguments(self):
        task = HelloBrainBox.new_task().sum(1, 2)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual('HelloBrainBox', task.decider)
        self.assertEqual('sum', task.method)
        self.assertEqual({'a': 1, 'b': 2}, task.arguments)
        self.assertEqual({}, task.dependencies)
        self.assertEqual([], task.fake_dependencies)
        self.assertEqual('', task.ordering_token)

    def test_brainboxtask_as_argument(self):
        other = HelloBrainBox.new_task().sum(3, 4)
        task = HelloBrainBox.new_task().sum(other, 5)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual({'a': other}, task.dependencies)
        self.assertEqual({'b': 5}, task.arguments)

    def test_both_arguments_as_tasks(self):
        task_a = HelloBrainBox.new_task().sum(1, 2)
        task_b = HelloBrainBox.new_task().sum(3, 4)
        task = HelloBrainBox.new_task().sum(task_a, task_b)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual({'a': task_a, 'b': task_b}, task.dependencies)
        self.assertEqual({}, task.arguments)

    def test_dependency_id(self):
        task = HelloBrainBox.new_task().sum(Dependency('my-id'), 2)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual({'a': 'my-id'}, task.dependencies)
        self.assertEqual({'b': 2}, task.arguments)

    def test_after(self):
        other = HelloBrainBox.new_task().sum(1, 2)
        task = HelloBrainBox.new_task().after(other).sum(3, 4)
        self.assertEqual((other,), task.fake_dependencies)
        self.assertEqual({'a': 3, 'b': 4}, task.arguments)

    def test_after_multiple(self):
        t1 = HelloBrainBox.new_task().sum(1, 2)
        t2 = HelloBrainBox.new_task().sum(3, 4)
        task = HelloBrainBox.new_task().after(t1, t2).sum(5, 6)
        self.assertEqual((t1, t2), task.fake_dependencies)

    def test_after_does_not_mutate_original(self):
        builder = HelloBrainBox.new_task()
        builder_with_after = builder.after(HelloBrainBox.new_task().sum(1, 2))
        task = builder.sum(3, 4)
        self.assertEqual([], task.fake_dependencies)

    def test_ordering_token(self):
        from brainbox.deciders.utils.hello_brainbox.api import HelloBrainBoxEntryPoint
        hbb = HelloBrainBoxEntryPoint()
        from brainbox.framework.task.entry_point import _parse_signatures_and_ctor
        sigs, ctor = _parse_signatures_and_ctor(hbb, ['a'])
        hbb._signatures = sigs
        hbb._ctor = ctor
        task = hbb.new_task().sum(7, 8)
        self.assertEqual('7', task.ordering_token)
