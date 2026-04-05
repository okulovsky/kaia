from collections.abc import Iterable
from pathlib import Path
from unittest import TestCase

from foundation_kaia.marshalling_2.marshalling.model import endpoint
from foundation_kaia.marshalling_2.marshalling.server import TestEndpointApi
from foundation_kaia.tests.test_marshalling_2.test_marshalling.test_server.common import sender, receiver, CHUNKS

SIGNAL_FILE = Path(__file__).parent / 'upload_signal'


@endpoint(verify_abstract=False)
def upload(data: Iterable[bytes]) -> None:
    receiver(SIGNAL_FILE, data)


class TestStreamUpload(TestCase):
    def setUp(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def tearDown(self):
        if SIGNAL_FILE.exists():
            SIGNAL_FILE.unlink()

    def test_upload_streams_chunk_by_chunk(self):
        with TestEndpointApi(upload) as api:
            api(sender(SIGNAL_FILE))
            data = SIGNAL_FILE.read_bytes()
            self.assertEqual(b''.join(CHUNKS), data)
