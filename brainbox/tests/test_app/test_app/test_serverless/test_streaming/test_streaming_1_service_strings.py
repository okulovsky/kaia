import uuid
from typing import Iterable
from unittest import TestCase

from brainbox.framework import BrainBox, ISelfManagingDecider
from brainbox.framework.common.streaming import StreamingStorage
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.app.serverless_test import ServerlessTest
from foundation_kaia.marshalling_2 import websocket, service

from .tool import run_streaming_process, _poll, _wait_for_responding, _read_lines


@service
class ByteToStringDecider(ISelfManagingDecider):
    """Reads bytes from a streaming input file and yields the string representation of each byte."""

    @websocket(verify_abstract=False)
    def _process(self, data: Iterable[bytes]) -> Iterable[str]:
        for chunk in data:
            for b in chunk:
                yield str(b)

    def process(self, input_filename: str) -> str:
        return run_streaming_process(self, input_filename)


class StreamingStringsTestCase(TestCase):

    def test_streaming_incremental(self):
        """
        Write 10 bytes without committing the input stream.
        The job must produce one string per byte, visible in the output file before commit.
        """
        with ServerlessTest(registry=ControllerRegistry([ByteToStringDecider()])) as api:
            storage = StreamingStorage(api.locator.cache_folder)
            input_filename = f'{uuid.uuid4()}.bin'
            storage.begin_writing(input_filename)

            task = BrainBox.TaskBuilder.call(ByteToStringDecider).process(input_filename)
            job_id = api.add(task)

            output_filename = _wait_for_responding(api, job_id)

            chunk = bytes(range(10))
            storage.append(input_filename, chunk)

            output = _read_lines(storage, output_filename, len(chunk))
            expected = [str(b) for b in chunk]
            self.assertEqual(expected, output)

            self.assertIsNone(
                api.tasks.get_job_summary(job_id).finished_timestamp,
                "Job should still be running (blocked on uncommitted input)",
            )

            storage.commit(input_filename)
            summary = _poll(api, job_id, lambda s: s.finished_timestamp is not None)
            self.assertTrue(summary.success, f"Job failed after commit:\n{api.tasks.get_error(job_id)}")
