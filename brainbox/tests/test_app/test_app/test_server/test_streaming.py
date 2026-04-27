import uuid
from unittest import TestCase

from brainbox.framework import BrainBox
from brainbox.framework.common.streaming import StreamingStorage
from brainbox.framework.app.api import BrainBoxApi

from brainbox.tests.test_app.test_app.test_serverless.test_streaming.tool import (
    IncrementingDecider, _poll, _wait_for_responding, _read_bytes,
)


class ServerStreamingTestCase(TestCase):

    def test_streaming_incremental(self):
        with BrainBoxApi.test([IncrementingDecider()], port=18191) as api:
            storage = StreamingStorage(api.debug_locations.cache_folder)
            input_filename = f'{uuid.uuid4()}.bin'
            storage.begin_writing(input_filename)

            task = BrainBox.TaskBuilder.call(IncrementingDecider).process(input_filename)
            job_id = api.add(task)

            output_filename = _wait_for_responding(api, job_id)

            chunk = bytes(range(10))
            storage.append(input_filename, chunk)  # write but do NOT commit

            output = _read_bytes(storage, output_filename, len(chunk))
            expected = bytes((b + 1) % 256 for b in chunk)
            self.assertEqual(expected, output, "Output bytes do not match incremented input")

            self.assertIsNone(
                api.tasks.get_job_summary(job_id).finished_timestamp,
                "Job should still be running (blocked on uncommitted input)",
            )

            storage.commit(input_filename)
            summary = _poll(api, job_id, lambda s: s.finished_timestamp is not None)
            self.assertTrue(summary.success, f"Job failed after commit:\n{api.tasks.get_error(job_id)}")
