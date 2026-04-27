import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from foundation_kaia.marshalling import FileLikeHandler


class TestToBytesIterable(unittest.TestCase):

    def test_bytes_chunked(self):
        chunks = list(FileLikeHandler.to_bytes_iterable(b'abcdefgh', chunk_size=3))
        self.assertEqual([b'abc', b'def', b'gh'], chunks)

    def test_bytesio_seeks_to_start(self):
        bio = BytesIO(b'abcdef')
        bio.read(2)  # advance cursor to verify seek(0) happens
        chunks = list(FileLikeHandler.to_bytes_iterable(bio, chunk_size=2))
        self.assertEqual([b'ab', b'cd', b'ef'], chunks)

    def test_path_chunked(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'abcdef')
            tmp.flush()
            path = Path(tmp.name)
        try:
            chunks = list(FileLikeHandler.to_bytes_iterable(path, chunk_size=2))
            self.assertEqual([b'ab', b'cd', b'ef'], chunks)
        finally:
            path.unlink()

    def test_str_path(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'hello')
            tmp.flush()
            path = tmp.name
        try:
            self.assertEqual(b'hello', b''.join(FileLikeHandler.to_bytes_iterable(path)))
        finally:
            Path(path).unlink()

    def test_iterable_of_bytes(self):
        chunks = list(FileLikeHandler.to_bytes_iterable(iter([b'hello', b' ', b'world'])))
        self.assertEqual([b'hello', b' ', b'world'], chunks)

    def test_iterable_of_str_encoded_as_utf8(self):
        chunks = list(FileLikeHandler.to_bytes_iterable(iter(['hel', 'lo'])))
        self.assertEqual([b'hel', b'lo'], chunks)

    def test_unsupported_type_raises(self):
        with self.assertRaises(ValueError):
            list(FileLikeHandler.to_bytes_iterable(42))


class TestToBytes(unittest.TestCase):
    def test_joins_chunks(self):
        self.assertEqual(b'abcdefgh', FileLikeHandler.to_bytes(b'abcdefgh'))


class TestWrite(unittest.TestCase):
    def test_writes_to_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            path = Path(tmp.name)
        try:
            FileLikeHandler.write(b'written', path)
            self.assertEqual(b'written', path.read_bytes())
        finally:
            path.unlink()


if __name__ == '__main__':
    unittest.main()
