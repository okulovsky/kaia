import unittest
from dataclasses import dataclass
from collections.abc import Iterable
from foundation_kaia.marshalling_2.marshalling.model import endpoint, FileLike
from .tool import make_content_test


@dataclass
class Data:
    value: int


class TestContent(unittest.TestCase):

    def test_json_only(self):
        @endpoint
        def func(p: Data) -> None: ...
        c, kw = make_content_test(func, Data(1))
        self.assertEqual({'p': Data(value=1)}, kw)

    def test_single_file(self):
        @endpoint
        def func(f: FileLike) -> None: ...
        c, kw = make_content_test(func, b'hello')
        self.assertEqual({'f': b'hello'}, kw)

    def test_two_files(self):
        @endpoint
        def func(f1: FileLike, f2: FileLike) -> None: ...
        c, kw = make_content_test(func, b'aaa', b'bbb')
        self.assertEqual({'f1': b'aaa', 'f2': b'bbb'}, kw)

    def test_json_and_file(self):
        @endpoint
        def func(p: Data, f: FileLike) -> None: ...
        c, kw = make_content_test(func, Data(5), b'data')
        self.assertEqual({'p': Data(value=5), 'f': b'data'}, kw)

    def test_json_and_two_files(self):
        @endpoint
        def func(p: Data, f1: FileLike, f2: FileLike) -> None: ...
        c, kw = make_content_test(func, Data(7), b'x', b'y')
        self.assertEqual({'p': Data(value=7), 'f1': b'x', 'f2': b'y'}, kw)

    def test_binary_stream(self):
        @endpoint
        def func(data: Iterable[bytes]) -> None: ...
        c, kw = make_content_test(func, iter([b'chunk1', b'chunk2']))
        self.assertEqual([b'chunk1', b'chunk2'], list(kw['data']))


if __name__ == '__main__':
    unittest.main()
