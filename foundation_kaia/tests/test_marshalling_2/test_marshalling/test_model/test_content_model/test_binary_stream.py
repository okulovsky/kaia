import unittest
from collections.abc import Iterable
from foundation_kaia.marshalling_2.marshalling.model import CallModel, endpoint


class TestBinaryStream(unittest.TestCase):

    def test_simple_binary_stream(self):
        @endpoint
        def func(data: Iterable[bytes]) -> None: ...
        it = iter([b'hello', b'world'])
        c = CallModel.Factory.test(func)(it).content
        self.assertIsNotNone(c.binary_stream)
        self.assertEqual('data', c.binary_stream.name)
        self.assertIs(it, c.binary_stream.iterable)
        self.assertIsNone(c.binary_stream.serializer)
        self.assertEqual('/func', c.url)
        self.assertEqual({}, c.json)
        self.assertEqual({}, c.files)

    def test_binary_stream_with_path_param(self):
        @endpoint
        def func(a: int, data: Iterable[bytes]) -> None: ...
        it = iter([b'x'])
        c = CallModel.Factory.test(func)(42, it).content
        self.assertEqual('/func/42', c.url)
        self.assertIsNotNone(c.binary_stream)
        self.assertEqual('data', c.binary_stream.name)
        self.assertIs(it, c.binary_stream.iterable)
        self.assertEqual({}, c.json)
        self.assertEqual({}, c.files)

    def test_binary_stream_with_query_param(self):
        @endpoint
        def func(a: int | None, data: Iterable[bytes]) -> None: ...
        it = iter([b'x'])
        c = CallModel.Factory.test(func)(7, it).content
        self.assertEqual('/func?a=7', c.url)
        self.assertIsNotNone(c.binary_stream)
        self.assertEqual('data', c.binary_stream.name)
        self.assertIs(it, c.binary_stream.iterable)
        self.assertEqual({}, c.json)
        self.assertEqual({}, c.files)

    def test_binary_stream_none_raises(self):
        @endpoint
        def func(data: Iterable[bytes]) -> None: ...
        with self.assertRaises(ValueError):
            CallModel.Factory.test(func)(None).content


if __name__ == '__main__':
    unittest.main()
