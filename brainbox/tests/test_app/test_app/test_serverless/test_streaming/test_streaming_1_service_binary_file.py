import uuid
from unittest import TestCase

from brainbox.framework import BrainBox
from brainbox.framework.common.streaming import StreamingStorage
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.app.serverless_test import ServerlessTest

from .tool import IncrementingDecider, _poll, _wait_for_responding, _read_bytes


class StreamingTestCase(TestCase):

    def test_streaming_incremental(self):
        """
        Write 10 bytes without committing the input stream.
        The job must process those bytes (visible in the output file) while still
        blocked waiting for more input — confirming true streaming behaviour.
        """
        with ServerlessTest(registry=ControllerRegistry([IncrementingDecider()])) as api:
            storage = StreamingStorage(api.debug_locations.cache_folder)
            input_filename = f'{uuid.uuid4()}.bin'
            storage.begin_writing(input_filename)

            task = BrainBox.TaskBuilder.call(IncrementingDecider).process(input_filename)
            job_id = api.add(task)

            output_filename = _wait_for_responding(api, job_id)

            chunk = bytes(range(10))
            storage.append(input_filename, chunk)

            output = _read_bytes(storage, output_filename, len(chunk))
            expected = bytes((b + 1) % 256 for b in chunk)
            self.assertEqual(expected, output)

            self.assertIsNone(
                api.tasks.get_job_summary(job_id).finished_timestamp,
                "Job should still be running (blocked on uncommitted input)",
            )

            storage.commit(input_filename)
            summary = _poll(api, job_id, lambda s: s.finished_timestamp is not None)
            self.assertTrue(summary.success, f"Job failed after commit:\n{api.tasks.get_error(job_id)}")

    def test_sentinel_causes_failure(self):
        """Feeding a 0xFF byte must cause the job to fail."""
        with ServerlessTest(registry=ControllerRegistry([IncrementingDecider()])) as api:
            storage = StreamingStorage(api.debug_locations.cache_folder)
            input_filename = f'{uuid.uuid4()}.bin'
            storage.begin_writing(input_filename)
            storage.append(input_filename, bytes([0x01, 0xFF, 0x02]))
            storage.commit(input_filename)

            task = BrainBox.TaskBuilder.call(IncrementingDecider).process(input_filename)
            job_id = api.add(task)

            summary = _poll(api, job_id, lambda s: s.finished_timestamp is not None)
            self.assertFalse(summary.success, "Job should have failed due to sentinel byte")
            self.assertIn('0xFF', api.tasks.get_error(job_id))
