import time
from brainbox.framework import ISelfManagingDecider
from brainbox.framework.common.streaming import StreamingStorage
from brainbox.framework.common import DeciderModel
from brainbox.framework.controllers import DockerMarshallingApiCall
from foundation_kaia.marshalling import websocket, service, ApiCall
from typing import Iterable


def run_streaming_process(decider: ISelfManagingDecider, input_filename: str) -> str:
    """Boilerplate for running a decider's _process endpoint locally via preprocess/call_locally/postprocess."""
    decider_model = DeciderModel.parse(type(decider))
    if len(decider_model.methods) != 1:
        raise ValueError("Expected exactly one endpoint name")
    method = decider_model.methods[list(decider_model.methods)[0]]
    api_call = ApiCall('', method.endpoint)
    dws_call = DockerMarshallingApiCall(decider, api_call, method)
    call_model = dws_call.preprocess(input_filename)
    result = call_model.call_locally(decider._process)
    return dws_call.postprocess(result)


@service
class IncrementingDecider(ISelfManagingDecider):
    """Reads bytes from a streaming input file and writes each byte incremented by 1.
    Raises ValueError if sentinel byte 0xFF is encountered."""

    @websocket(verify_abstract=False)
    def _process(self, data: Iterable[bytes]) -> Iterable[bytes]:
        for chunk in data:
            if 0xFF in chunk:
                raise ValueError(f"Sentinel byte 0xFF encountered in chunk")
            incremented = bytes((b + 1) % 256 for b in chunk)
            yield incremented

    def process(self, input_filename: str) -> str:
        return run_streaming_process(self, input_filename)


def _poll(api, job_id, condition, steps=10, delay=0.1):
    for _ in range(steps):
        time.sleep(delay)
        summary = api.tasks.get_job_summary(job_id)
        if condition(summary):
            return summary
    raise ValueError("_poll failed to wait for condition")


def _wait_for_responding(api, job_id: str):
    """Poll until the job calls report_responding, then return the output filename."""
    summary = _poll(
        api, job_id,
        lambda s: s.responding_timestamp is not None or s.finished_timestamp is not None
    )
    if summary.finished_timestamp is not None:
        raise AssertionError(f"Job {job_id} finished unexpectedly:\n{api.tasks.get_error(job_id)}")
    if summary.responding_timestamp is None:
        raise AssertionError(f"Job {job_id} never called report_responding (timeout)")
    output_filename = api.tasks.get_result(job_id)
    if output_filename is None:
        raise AssertionError(f"Job {job_id} output filename not set by report_responding")
    return output_filename


def _read_bytes(storage: StreamingStorage, filename: str, n: int, timeout: float = 5.0) -> bytes:
    """Read exactly n bytes from a streaming file, stopping after timeout seconds of inactivity."""
    result = b''
    for chunk in storage.read(filename, timeout=timeout):
        result += chunk
        if len(result) > n:
            raise ValueError(f"Too many bytes read, expected {n}, actual {len(result)}")
        elif len(result) == n:
            return result
    return result


def _read_lines(storage: StreamingStorage, filename: str, n: int, timeout: float = 5.0) -> list[str]:
    """Read exactly n newline-terminated lines from a streaming file."""
    buffer = b''
    lines = []
    for chunk in storage.read(filename, timeout=timeout):
        buffer += chunk
        while b'\n' in buffer:
            line, buffer = buffer.split(b'\n', 1)
            lines.append(line.decode('utf-8'))
            if len(lines) == n:
                return lines
    return lines
