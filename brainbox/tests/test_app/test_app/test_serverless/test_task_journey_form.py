from unittest import TestCase
from brainbox.deciders.utils.hello_brainbox import HelloBrainBox
from brainbox.framework.brainbox import BrainBoxApi
from brainbox.framework.app.serverless_test import ServerlessTest
from brainbox.framework.controllers.architecture import ControllerRegistry



def _make(api: BrainBoxApi, task):
    id = api.add(task)
    api.tasks.base_join([id], ignore_errors=True)
    log = api.diagnostics.operator_log()
    journey = [i.event for i in log if i.level == i.Level.Task and i.id == id]
    return journey


class TestHelloBrainBoxTrainingLastMessage(TestCase):
    def test_task_journey(self):
        with ServerlessTest(registry=ControllerRegistry([HelloBrainBox])) as api:
            for i in range(10):
                journey = _make(api, HelloBrainBox.new_task().sum(2,3))
                self.assertEqual(
                    ['Assigned', 'Accepted', 'Finished with a success'],
                    journey
                )

            journey = _make(api, HelloBrainBox.new_task().training(b'abcd'))
            self.assertEqual(
                ['Assigned', 'Accepted', 'Responding', 'Finished with a success'],
                journey
            )

            journey = _make(api, HelloBrainBox.new_task().training(b'abcd', raise_exception=True))
            self.assertEqual(
                ['Assigned', 'Accepted', 'Responding', 'Finished with a failure'],
                journey
            )







