from brainbox.framework import BrainBoxTask, BrainBoxCombinedTask, IDecider
from unittest import TestCase


class Test(IDecider):
    def method(self, a, b):
        return a+b

    def warmup(self, parameters: str):
        pass

    def cooldown(self, parameters: str):
        pass


class CoolCtorTestCase(TestCase):
    def test_simple_ctor(self):
        task = BrainBoxTask(decider='Test', decider_method='method', arguments=dict(a=5, b=6))
        job = task.create_jobs()[0]
        self.assertEqual(job.id, task.id)
        self.assertEqual(job.decider, 'Test')
        self.assertEqual(job.method, 'method')
        self.assertDictEqual(dict(a=5, b=6), job.arguments)


    def test_ctor_with_type_and_method(self):
        task = BrainBoxTask(id = BrainBoxTask.safe_id(), decider=Test, decider_method=Test.method, arguments=dict(a=5, b=6))
        job = task.create_jobs()[0]
        self.assertEqual(job.id, task.id)
        self.assertEqual(job.decider, 'Test')
        self.assertEqual(job.method, 'method')
        self.assertDictEqual(dict(a=5, b=6), job.arguments)

        self.assertRaises(Exception, lambda: BrainBoxTask(decider=Test, decider_method=Test.method, arguments=dict(x=2)))


    def test_ctor_with_method_only(self):
        task = BrainBoxTask(decider=Test.method, arguments=dict(a=5, b=6))
        job = task.create_jobs()[0]
        self.assertEqual(job.id, task.id)
        self.assertEqual(job.decider, 'Test')
        self.assertEqual(job.method, 'method')
        self.assertDictEqual(dict(a=5, b=6), job.arguments)
        self.assertRaises(Exception, lambda: BrainBoxTask(decider=Test.method, arguments=dict(x=2)))

    def test_arguments_exceptions(self):
        self.assertRaises(Exception, lambda: BrainBoxTask(decider=Test.method, arguments=dict(x=2)))
        self.assertRaises(Exception, lambda: BrainBoxTask(decider=Test, decider_method=Test.method, arguments=dict(x=2)))

    def test_dependency(self):
        task = BrainBoxTask(decider=Test.method, arguments=dict(a=3, b=6), id='test')
        task_2 = BrainBoxTask(decider=Test.method, arguments=dict(a=task, b=4), id='test_2')
        self.assertEqual('test', task_2.dependencies['a'])

        pack = BrainBoxCombinedTask(task, ())
        task_3 = BrainBoxTask(decider=Test.method, arguments=dict(a=task_2, b=pack))
        self.assertEqual('test', task_3.dependencies['b'])
        self.assertEqual('test_2', task_3.dependencies['a'])

    def test_fake_dependency(self):
        task = BrainBoxTask(decider=Test.method, arguments=dict(a=3, b=6), id='test')
        task_2 = BrainBoxTask(decider=Test.method, arguments=dict(a=2, b=4), fake_dependencies=[task])
        self.assertDictEqual({'*fake_dependency_0': 'test'}, task_2.dependencies)








