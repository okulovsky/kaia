import uuid
from unittest import TestCase

from brainbox.framework import BrainBox, AlwaysOnPlanner
from brainbox.framework.task.task_builder import Dependency
from brainbox.framework.common.streaming import StreamingStorage
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.app.serverless_test import ServerlessTest

from .tool import IncrementingDecider, _poll, _wait_for_responding, _read_bytes


class SecondIncrementingDecider(IncrementingDecider):
    pass


class TwoServicesStreamingTestCase(TestCase):

    def test_pipeline_incremental(self):
        """
        Two IncrementingDeciders chained: the second consumes the output of the first.
        Both jobs start streaming before the input is committed, confirming a true
        concurrent pipeline: input → job1 → job2 → final output.
        AlwaysOnPlanner is required because SimplePlanner supports only one active decider.
        """
        with ServerlessTest(
            registry=ControllerRegistry([IncrementingDecider(), SecondIncrementingDecider()]),
            planner=AlwaysOnPlanner(),
        ) as api:
            storage = StreamingStorage(api.locator.cache_folder)
            input_filename = f'{uuid.uuid4()}.bin'
            storage.begin_writing(input_filename)

            task1 = BrainBox.TaskBuilder.call(IncrementingDecider).process(input_filename)
            job_id1 = api.add(task1)
            task2 = BrainBox.TaskBuilder.call(SecondIncrementingDecider).process(Dependency(job_id1))
            job_id2 = api.add(task2)

            _wait_for_responding(api, job_id1)
            final_filename = _wait_for_responding(api, job_id2)

            chunk = bytes(range(10))
            storage.append(input_filename, chunk)

            expected = bytes((b + 2) % 256 for b in chunk)
            output = _read_bytes(storage, final_filename, len(chunk))
            self.assertEqual(expected, output)

            self.assertIsNone(api.tasks.get_job_summary(job_id1).finished_timestamp, "Job 1 should still be running")
            self.assertIsNone(api.tasks.get_job_summary(job_id2).finished_timestamp, "Job 2 should still be running")

            storage.commit(input_filename)
            summary2 = _poll(api, job_id2, lambda s: s.finished_timestamp is not None)
            self.assertTrue(summary2.success, f"Job 2 failed after commit:\n{api.tasks.get_error(job_id2)}")
