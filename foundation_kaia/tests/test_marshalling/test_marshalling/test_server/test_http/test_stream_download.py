from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from unittest import TestCase

from foundation_kaia.marshalling import endpoint, TestEndpointApi
from foundation_kaia.tests.test_marshalling.test_marshalling.test_server.common import sender, receiver, CHUNKS

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


@endpoint(verify_abstract=False)
def string_stream() -> Iterable[str]:
    yield 'hello'
    yield 'world'
    yield ''
    yield 'done'


class TestStringIterable(TestCase):
    def test_yields_strings(self):
        with TestEndpointApi(string_stream, port=11513) as api:
            result = list(api())
        self.assertEqual(['hello', 'world', '', 'done'], result)


@dataclass
class _Point:
    x: int
    y: int


@endpoint(verify_abstract=False)
def custom_stream() -> Iterable[_Point]:
    yield _Point(1, 2)
    yield _Point(3, 4)
    yield _Point(5, 6)


class TestCustomIterable(TestCase):
    def test_yields_typed_objects(self):
        with TestEndpointApi(custom_stream, port=11514) as api:
            result = list(api())
        self.assertEqual([_Point(1, 2), _Point(3, 4), _Point(5, 6)], result)
