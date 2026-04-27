import unittest
from foundation_kaia.marshalling import CallModel, endpoint, ContentModel
from foundation_kaia.tests.test_marshalling.test_marshalling.test_model.test_content_model.tool import make_url_test


class TestPrimitivesInPath(unittest.TestCase):
    def check_no_content(self, c: ContentModel):
        self.assertEqual({}, c.json)
        self.assertEqual({}, c.files)
        self.assertIsNone(c.binary_stream)

    def test_int_in_url_path(self):
        @endpoint
        def func(a: int) -> None: ...
        c, data = make_url_test(func, 42)
        self.assertEqual('/func/42', c.url)
        self.check_no_content(c)
        self.assertEqual({'a': 42}, data)

    def test_str_in_url_path(self):
        @endpoint
        def my_func(name: str) -> None: ...
        c, data = make_url_test(my_func, 'hello')
        self.assertEqual('/my-func/hello', c.url)
        self.check_no_content(c)
        self.assertEqual({'name': 'hello'}, data)

    def test_float_in_url_path(self):
        @endpoint
        def func(x: float) -> None: ...
        c, data = make_url_test(func, 3.14)
        self.assertEqual('/func/3.14', c.url)
        self.check_no_content(c)
        self.assertEqual({'x': 3.14}, data)

    def test_multiple_primitives_appear_in_order(self):
        @endpoint
        def func(a: int, b: str) -> None: ...
        c, data = make_url_test(func, 1, 'x')
        self.assertEqual('/func/1/x', c.url)
        self.check_no_content(c)
        self.assertEqual({'a': 1, 'b': 'x'}, data)

    def test_default_used_for_missing_primitive(self):
        @endpoint
        def func(a: int, b: str = 'world') -> None: ...
        c, data = make_url_test(func, 5)
        self.assertEqual('/func/5/world', c.url)
        self.check_no_content(c)
        self.assertEqual({'a': 5, 'b': 'world'}, data)

    def test_no_json_no_files_for_primitives(self):
        @endpoint
        def func(a: int, b: str) -> None: ...
        c, data = make_url_test(func, 1, 'x')
        self.check_no_content(c)
        self.assertEqual({'a': 1, 'b': 'x'}, data)


if __name__ == '__main__':
    unittest.main()
