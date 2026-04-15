from unittest import TestCase
from brainbox.deciders.utils.hello_brainbox.api import HelloBrainBoxApi
from brainbox.framework import BrainBox, BrainBoxTask, Dependency



class LegacyTaskBuilderTestCase(TestCase):
    def _call(self, **kwargs):
        return BrainBox.TaskBuilder.call(HelloBrainBoxApi, **kwargs)

    def test_plain_arguments(self):
        task = self._call().sum(1, 2)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual('HelloBrainBoxApi', task.decider)
        self.assertEqual('sum', task.method)
        self.assertEqual({'a': 1, 'b': 2}, task.arguments)
        self.assertEqual({}, task.dependencies)
        self.assertEqual([], task.fake_dependencies)
        self.assertEqual('', task.ordering_token)

    def test_brainboxtask_as_argument(self):
        other = self._call().sum(3, 4)
        task = self._call().sum(other, 5)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual({'a': other}, task.dependencies)
        self.assertEqual({'b': 5}, task.arguments)

    def test_both_arguments_as_tasks(self):
        task_a = self._call().sum(1, 2)
        task_b = self._call().sum(3, 4)
        task = self._call().sum(task_a, task_b)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual({'a': task_a, 'b': task_b}, task.dependencies)
        self.assertEqual({}, task.arguments)

    def test_dependency_id(self):
        task = self._call().sum(Dependency('my-id'), 2)
        self.assertIsInstance(task, BrainBoxTask)
        self.assertEqual({'a': 'my-id'}, task.dependencies)
        self.assertEqual({'b': 2}, task.arguments)

    def test_after(self):
        other = self._call().sum(1, 2)
        task = self._call().after(other).sum(3, 4)
        self.assertEqual((other,), task.fake_dependencies)
        self.assertEqual({'a': 3, 'b': 4}, task.arguments)

    def test_after_multiple(self):
        t1 = self._call().sum(1, 2)
        t2 = self._call().sum(3, 4)
        task = self._call().after(t1, t2).sum(5, 6)
        self.assertEqual((t1, t2), task.fake_dependencies)

    def test_after_does_not_mutate_original(self):
        builder = self._call()
        builder.after(self._call().sum(1, 2))
        task = builder.sum(3, 4)
        self.assertEqual([], task.fake_dependencies)

    def test_non_service_method_available(self):
        # LegacyTaskBuilder picks up ALL public methods, not just @brainbox_endpoint ones
        # load_model comes from IModelLoadingSupport which is @service, but this verifies
        # that methods not in the @service interface of HelloBrainBoxApi are also present
        sigs = BrainBox.TaskBuilder.call(HelloBrainBoxApi)._signatures
        self.assertIn('sum', sigs)
        self.assertIn('load_model', sigs)
        self.assertIn('download_model', sigs)
