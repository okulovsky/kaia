from brainbox.framework import BrainBoxTask, IBrainBoxTask, IDecider
from unittest import TestCase
from typing import cast

class Test(IDecider):
    def method(self, required_1, required_2, optional_1 = None, optional_2 = 'b', **kwargs):
        pass

    @classmethod
    def get_ordering_arguments_sequence(cls) -> tuple[str,...]|None:
        return 'optional_1', 'required_1'


class TaskBuilderTestCase(TestCase):

    def test_task_builder(self):
        task = BrainBoxTask.build(BrainBoxTask.call(Test).method(required_1=4,required_2=5))
        for job in [task.create_jobs()[0], task.to_task().create_jobs()[0]]:
            job = task.create_jobs()[0]
            self.assertEqual('Test', job.decider)
            self.assertEqual('method', job.method)
            self.assertDictEqual(dict(required_1=4, required_2=5), job.arguments)

    def test_task_builder_validates_parameters(self):
        self.assertRaises(TypeError, lambda: BrainBoxTask.call(Test).method(x=4))

    def test_task_builder_with_args(self):
        task: IBrainBoxTask = BrainBoxTask.build(BrainBoxTask.call(Test).method(2, 3))
        self.assertDictEqual(
            dict(required_1=2, required_2=3),
            task.create_jobs()[0].arguments
        )

        task: IBrainBoxTask = BrainBoxTask.build(BrainBoxTask.call(Test).method(2, 3, 4))
        self.assertDictEqual(
            dict(required_1=2, required_2=3, optional_1=4),
            task.create_jobs()[0].arguments
        )

        task = BrainBoxTask.build(BrainBoxTask.call(Test).method(2, required_2=3, optional_1=4))
        self.assertDictEqual(
            dict(required_1=2, required_2=3, optional_1=4),
            task.create_jobs()[0].arguments
        )

        self.assertRaises(
            Exception,
            lambda: BrainBoxTask.call(Test).method(4)
        )

        self.assertRaises(
            Exception,
            lambda: BrainBoxTask.call(Test).method(2,3,required_1=4)
        )

    def test_task_builder_with_ordering_token(self):
        task = BrainBoxTask.build(BrainBoxTask.call(Test).method(1, 2, 3, '4'))
        self.assertEqual('3/1', task.create_jobs()[0].ordering_token)

        task = BrainBoxTask.build(BrainBoxTask.call(Test).method(
            required_1=1,
            required_2=2,
            optional_2='4',
        ))
        self.assertEqual('*/1', task.create_jobs()[0].ordering_token)

    def test_task_fake_dependencies(self):
        task_1 = BrainBoxTask.build(BrainBoxTask.call(Test).method(3,4)).to_task(id='test')
        task_2 = (
            BrainBoxTask.build(BrainBoxTask.call(Test).method(1,2))
            .dependent_on(task_1)
        )
        self.assertDictEqual({'*fake_dependency_0': 'test'}, task_2.create_jobs()[0].dependencies)

