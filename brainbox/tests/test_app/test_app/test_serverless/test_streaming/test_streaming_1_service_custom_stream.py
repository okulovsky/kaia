import json
import uuid
from dataclasses import dataclass
from typing import Iterable
from unittest import TestCase

from brainbox.framework import BrainBox, ISelfManagingDecider
from brainbox.framework.common.streaming import StreamingStorage
from brainbox.framework.controllers.architecture import ControllerRegistry
from brainbox.framework.app.serverless_test import ServerlessTest
from foundation_kaia.marshalling_2 import websocket, service

from .tool import run_streaming_process, _poll


@dataclass
class ByteRecord:
    value: int


@service
class ByteToRecordDecider(ISelfManagingDecider):
    """Reads bytes from a streaming input file and yields a ByteRecord for each byte."""

    @websocket(verify_abstract=False)
    def _process(self, data: Iterable[bytes]) -> Iterable[ByteRecord]:
        for chunk in data:
            for b in chunk:
                yield ByteRecord(value=b)

    def process(self, input_filename: str) -> str:
        return run_streaming_process(self, input_filename)


class StreamingCustomStreamTestCase(TestCase):

    def test_streaming_success(self):
        """Commit input upfront; job produces one ByteRecord per byte in JSONL format."""
        with ServerlessTest(registry=ControllerRegistry([ByteToRecordDecider()])) as api:
            storage = StreamingStorage(api.debug_locations.cache_folder)
            input_filename = f'{uuid.uuid4()}.bin'
            storage.begin_writing(input_filename)
            chunk = bytes(range(10))
            storage.append(input_filename, chunk)
            storage.commit(input_filename)

            task = BrainBox.TaskBuilder.call(ByteToRecordDecider).process(input_filename)
            job_id = api.add(task)

            summary = _poll(api, job_id, lambda s: s.finished_timestamp is not None)
            self.assertTrue(summary.success, f"Job failed:\n{api.tasks.get_error(job_id)}")

            output_filename = api.tasks.get_result(job_id)
            raw = b''.join(storage.read(output_filename))
            records = [json.loads(line) for line in raw.split(b'\n') if line]
            expected = [{'value': b} for b in chunk]
            self.assertEqual(expected, records)
