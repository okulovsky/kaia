import unittest
from dataclasses import dataclass
from foundation_kaia.marshalling import CallModel, endpoint, FileLike


class TestFiles(unittest.TestCase):

    def test_single_file(self):
        @endpoint
        def func(f: FileLike) -> None: ...
        c = CallModel.Factory.test(func)(b'data').content
        self.assertEqual({'f': b'data'}, c.raw_values)

    def test_two_files(self):
        @endpoint
        def func(f1: FileLike, f2: FileLike) -> None: ...
        c = CallModel.Factory.test(func)(b'data1', b'data2').content
        self.assertEqual({'f1': b'data1', 'f2': b'data2'}, c.raw_values)

    def test_all_together(self):
        @dataclass
        class Meta:
            name: str

        @endpoint
        def func(a: int, b: str | None, f: FileLike, meta: Meta) -> None: ...
        c = CallModel.Factory.test(func)(12, 'query', b'data', Meta('test')).content
        self.assertEqual({'f': b'data'}, c.raw_values)
        self.assertEqual({'meta': {'name': 'test'}}, c.json_values)
        self.assertEqual('/func/12?b=query', c.url)

    def test_file_not_provided_raises(self):
        @endpoint
        def func(f: FileLike) -> None: ...
        with self.assertRaises(TypeError):
            CallModel.Factory.test(func)().content

    def test_file_provided_as_none_raises(self):
        @endpoint
        def func(f: FileLike) -> None: ...
        with self.assertRaises(ValueError):
            CallModel.Factory.test(func)(None).content


if __name__ == '__main__':
    unittest.main()
