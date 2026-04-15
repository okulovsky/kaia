from unittest import TestCase
from brainbox.deciders.utils.hello_brainbox.api import HelloBrainBox
from brainbox.framework import JobRequest, Dependency


class JobRequestFromTaskTestCase(TestCase):
    def test_simple_task(self):
        task = HelloBrainBox.new_task(id='my-id', parameter='p', batch='b').sum(1, 2)
        requests = task.to_job_request()
        self.assertEqual(1, len(requests.jobs))
        r = requests.jobs[0]
        self.assertEqual('my-id', r.id)
        self.assertEqual('HelloBrainBox', r.decider)
        self.assertEqual('sum', r.method)
        self.assertEqual('p', r.parameter)
        self.assertEqual('b', r.batch)
        self.assertEqual({'a': 1, 'b': 2}, r.arguments)
        self.assertEqual({}, r.dependencies)

    def test_auto_id_assigned(self):
        task = HelloBrainBox.new_task().sum(1, 2)
        requests: JobRequest = task.to_job_request()
        self.assertEqual(1, len(requests.jobs))
        self.assertIsNotNone(requests.jobs[0].id)
        self.assertNotEqual('', requests.jobs[0].id)

    def test_task_dependency(self):
        dep_task = HelloBrainBox.new_task(id='dep-id').sum(1, 2)
        main_task = HelloBrainBox.new_task(id='main-id').sum(dep_task, 3)
        requests = main_task.to_job_request()
        self.assertEqual(2, len(requests.jobs))
        # dep comes first (topological order)
        main_req, dep_req = requests.jobs
        self.assertEqual('dep-id', dep_req.id)
        self.assertEqual('main-id', main_req.id)
        self.assertEqual({'a': 'dep-id'}, main_req.dependencies)
        self.assertEqual({'b': 3}, main_req.arguments)

    def test_shared_dependency_not_duplicated(self):
        shared = HelloBrainBox.new_task(id='shared-id').sum(1, 2)
        t1 = HelloBrainBox.new_task(id='t1').sum(shared, 3)
        t2 = HelloBrainBox.new_task(id='t2').sum(shared, 4)
        top = HelloBrainBox.new_task(id='top').sum(t1, t2)
        requests = top.to_job_request()
        ids = [r.id for r in requests.jobs]
        self.assertEqual(1, ids.count('shared-id'))
        self.assertEqual(4, len(requests.jobs))

    def test_fake_dependency_via_after(self):
        blocker = HelloBrainBox.new_task(id='blocker-id').sum(1, 2)
        main_task = HelloBrainBox.new_task(id='main-id').after(blocker).sum(3, 4)
        requests = main_task.to_job_request()
        self.assertEqual(2, len(requests.jobs))
        main_req, blocker_req = requests.jobs
        self.assertEqual('blocker-id', blocker_req.id)
        self.assertIn('*fake_dependency_0', main_req.dependencies)
        self.assertEqual('blocker-id', main_req.dependencies['*fake_dependency_0'])

    def test_string_dependency_id(self):
        task = HelloBrainBox.new_task(id='main-id').sum(Dependency('external-id'), 5)
        requests = task.to_job_request()
        self.assertEqual(1, len(requests.jobs))
        self.assertEqual({'a': 'external-id'}, requests.jobs[0].dependencies)
