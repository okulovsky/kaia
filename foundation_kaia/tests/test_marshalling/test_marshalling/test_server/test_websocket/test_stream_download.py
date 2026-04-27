from collections.abc import Iterable
from pathlib import Path
from unittest import TestCase

from foundation_kaia.marshalling import websocket, TestEndpointApi
from foundation_kaia.tests.test_marshalling.test_marshalling.test_server.common import sender, receiver, CHUNKS

SIGNAL_FILE = Path(__file__).parent / 'ws_download_signal'


@websocket(verify_abstract=False)
def download() -> Iterable[bytes]:
    return sender(SIGNAL_FILE)

class TestWsStreamDownload(TestCase):
    def setUp(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def tearDown(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def test_download_streams_chunk_by_chunk(self):
        with TestEndpointApi(download) as api:
            receiver(SIGNAL_FILE, api())
            self.assertEqual(b''.join(CHUNKS), SIGNAL_FILE.read_bytes())
