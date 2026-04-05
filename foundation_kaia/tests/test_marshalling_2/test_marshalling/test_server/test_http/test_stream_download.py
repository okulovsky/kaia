from collections.abc import Iterable
from pathlib import Path
from unittest import TestCase

from foundation_kaia.marshalling_2.marshalling.model import endpoint, EndpointModel
from foundation_kaia.marshalling_2.marshalling.server import Server, TestEndpointApi, ApiCall, TestApi
from foundation_kaia.tests.test_marshalling_2.test_marshalling.test_server.common import sender, receiver, CHUNKS

SIGNAL_FILE = Path(__file__).parent / 'download_signal'


@endpoint(verify_abstract=False)
def download() -> Iterable[bytes]:
    return sender(SIGNAL_FILE)


class TestStreamDownload(TestCase):
    def setUp(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def tearDown(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def test_download_streams_chunk_by_chunk(self):
        with TestEndpointApi(download) as api:
            result = api()

            receiver(SIGNAL_FILE, result)

            data = SIGNAL_FILE.read_bytes()
            self.assertEqual(b''.join(CHUNKS), data)
