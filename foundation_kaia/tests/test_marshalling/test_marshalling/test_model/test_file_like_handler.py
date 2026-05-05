import tempfile
import unittest
from dataclasses import dataclass
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


class TestToJsonlinesIterable(unittest.TestCase):

    def test_single_object(self):
        data = b'{"a": 1}\n'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}], result)

    def test_multiple_objects(self):
        data = b'{"a": 1}\n{"b": 2}\n{"c": 3}\n'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}, {"b": 2}, {"c": 3}], result)

    def test_chunked_across_newline(self):
        chunks = iter([b'{"x":', b' 1}\n{"y"', b': 2}\n'])
        result = list(FileLikeHandler.to_jsonlines_iterable(chunks))
        self.assertEqual([{"x": 1}, {"y": 2}], result)

    def test_empty_lines_skipped(self):
        data = b'{"a": 1}\n\n{"b": 2}\n'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}, {"b": 2}], result)

    def test_no_trailing_newline(self):
        data = b'{"a": 1}\n{"b": 2}'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}, {"b": 2}], result)


@dataclass
class _Point:
    x: int
    y: int


class TestToJsonlinesIterable(unittest.TestCase):

    def test_single_object(self):
        data = b'{"a": 1}\n'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}], result)

    def test_multiple_objects(self):
        data = b'{"a": 1}\n{"b": 2}\n{"c": 3}\n'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}, {"b": 2}, {"c": 3}], result)

    def test_chunked_across_newline(self):
        chunks = iter([b'{"x":', b' 1}\n{"y"', b': 2}\n'])
        result = list(FileLikeHandler.to_jsonlines_iterable(chunks))
        self.assertEqual([{"x": 1}, {"y": 2}], result)

    def test_empty_lines_skipped(self):
        data = b'{"a": 1}\n\n{"b": 2}\n'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}, {"b": 2}], result)

    def test_no_trailing_newline(self):
        data = b'{"a": 1}\n{"b": 2}'
        result = list(FileLikeHandler.to_jsonlines_iterable(data))
        self.assertEqual([{"a": 1}, {"b": 2}], result)


class TestToTypedJsonlinesIterable(unittest.TestCase):

    def test_deserializes_dataclass(self):
        data = b'{"x": 1, "y": 2}\n{"x": 3, "y": 4}\n'
        result = list(FileLikeHandler.to_typed_jsonlines_iterable(data, _Point))
        self.assertEqual([_Point(1, 2), _Point(3, 4)], result)

    def test_no_trailing_newline(self):
        data = b'{"x": 1, "y": 2}\n{"x": 3, "y": 4}'
        result = list(FileLikeHandler.to_typed_jsonlines_iterable(data, _Point))
        self.assertEqual([_Point(1, 2), _Point(3, 4)], result)

    def test_chunked(self):
        chunks = iter([b'{"x": 1,', b' "y": 2}\n', b'{"x": 3, "y": 4}\n'])
        result = list(FileLikeHandler.to_typed_jsonlines_iterable(chunks, _Point))
        self.assertEqual([_Point(1, 2), _Point(3, 4)], result)


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
