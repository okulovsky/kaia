from collections.abc import Iterable
from pathlib import Path
from unittest import TestCase

from foundation_kaia.marshalling import websocket, TestEndpointApi
from foundation_kaia.tests.test_marshalling.test_marshalling.test_server.common import sender, CHUNKS

SIGNAL_FILE = Path(__file__).parent / 'ws_roundtrip_signal'


@websocket(verify_abstract=False)
def echo(data: Iterable[bytes]) -> Iterable[bytes]:
    with open(SIGNAL_FILE, 'wb') as f:
        for chunk in data:
            f.write(chunk)
            f.flush()
            yield chunk


class TestWsStreamRoundtrip(TestCase):
    """
    A streaming input and a streaming output at once, e.g. a speech recognition that yields the results
    while the audio is still arriving: each chunk must be processed before the next one is sent.
    """
    def setUp(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def tearDown(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def test_roundtrip_processes_chunk_by_chunk(self):
        with TestEndpointApi(echo) as api:
            result = b''.join(api(sender(SIGNAL_FILE)))
            self.assertEqual(b''.join(CHUNKS), result)
