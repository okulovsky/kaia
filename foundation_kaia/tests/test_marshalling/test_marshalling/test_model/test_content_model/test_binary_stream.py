import unittest
from collections.abc import Iterable
from foundation_kaia.marshalling import CallModel, endpoint


class TestBinaryStream(unittest.TestCase):

    def test_simple_binary_stream(self):
        @endpoint
        def func(data: Iterable[bytes]) -> None: ...
        it = iter([b'hello', b'world'])
        c = CallModel.Factory.test(func)(it).content
        self.assertIn('data', c.raw_values)
        self.assertIs(it, c.raw_values['data'])
        self.assertEqual('/func', c.url)
        self.assertEqual({}, c.json_values)

    def test_binary_stream_with_path_param(self):
        @endpoint
        def func(a: int, data: Iterable[bytes]) -> None: ...
        it = iter([b'x'])
        c = CallModel.Factory.test(func)(42, it).content
        self.assertEqual('/func/42', c.url)
        self.assertIn('data', c.raw_values)
        self.assertIs(it, c.raw_values['data'])
        self.assertEqual({}, c.json_values)

    def test_binary_stream_with_query_param(self):
        @endpoint
        def func(a: int | None, data: Iterable[bytes]) -> None: ...
        it = iter([b'x'])
        c = CallModel.Factory.test(func)(7, it).content
        self.assertEqual('/func?a=7', c.url)
        self.assertIn('data', c.raw_values)
        self.assertIs(it, c.raw_values['data'])
        self.assertEqual({}, c.json_values)

    def test_binary_stream_none_raises(self):
        @endpoint
        def func(data: Iterable[bytes]) -> None: ...
        with self.assertRaises(ValueError):
            CallModel.Factory.test(func)(None).content


if __name__ == '__main__':
    unittest.main()
