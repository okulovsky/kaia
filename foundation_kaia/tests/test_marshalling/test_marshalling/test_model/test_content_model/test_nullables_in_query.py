import unittest
from foundation_kaia.marshalling import ContentModel, endpoint
from foundation_kaia.tests.test_marshalling.test_marshalling.test_model.test_content_model.tool import make_url_test


class TestNullablesInQuery(unittest.TestCase):
    def check_no_content(self, c: ContentModel):
        self.assertEqual({}, c.json)
        self.assertEqual({}, c.files)
        self.assertIsNone(c.binary_stream)

    def test_nullable_with_value_in_query_string(self):
        @endpoint
        def func(name: str | None) -> None: ...
        c, data = make_url_test(func, 'alice')
        self.assertEqual('/func?name=alice', c.url)
        self.check_no_content(c)
        self.assertEqual({'name': 'alice'}, data)

    def test_nullable_with_none_omitted_from_url(self):
        @endpoint
        def func(name: str | None) -> None: ...
        c, data = make_url_test(func, None)
        self.assertEqual('/func', c.url)
        self.check_no_content(c)
        self.assertEqual({}, data)

    def test_nullable_not_provided_omitted_from_url(self):
        @endpoint
        def func(a: int, name: str | None = None) -> None: ...
        c, data = make_url_test(func, 5)
        self.assertEqual('/func/5', c.url)
        self.check_no_content(c)
        self.assertEqual({'a': 5, 'name': None}, data)

    def test_nullable_in_query_not_in_path(self):
        @endpoint
        def func(name: str | None) -> None: ...
        c, data = make_url_test(func, 'bob')
        self.assertEqual('/func?name=bob', c.url)
        self.check_no_content(c)
        self.assertEqual({'name': 'bob'}, data)

    def test_multiple_query_params_partial(self):
        @endpoint
        def func(a: str | None, b: str | None) -> None: ...
        c, data = make_url_test(func, 'x', None)
        self.assertEqual('/func?a=x', c.url)
        self.check_no_content(c)
        self.assertEqual({'a': 'x'}, data)

    def test_nullable_int_with_value(self):
        @endpoint
        def func(count: int | None) -> None: ...
        c, data = make_url_test(func, 7)
        self.assertEqual('/func?count=7', c.url)
        self.check_no_content(c)
        self.assertEqual({'count': 7}, data)

    def test_no_json_no_files_for_nullable(self):
        @endpoint
        def func(name: str | None) -> None: ...
        c, data = make_url_test(func, 'alice')
        self.assertEqual({}, c.json)
        self.assertEqual({}, c.files)
        self.check_no_content(c)
        self.assertEqual({'name': 'alice'}, data)

    def test_nullable_with_non_none_default_not_provided(self):
        @endpoint
        def func(name: str | None = 'default') -> None: ...
        c, data = make_url_test(func)
        self.assertEqual('/func?name=default', c.url)
        self.check_no_content(c)
        self.assertEqual({'name': 'default'}, data)

    def test_nullable_with_non_none_default_overridden(self):
        @endpoint
        def func(name: str | None = 'default') -> None: ...
        c, data = make_url_test(func, 'alice')
        self.assertEqual('/func?name=alice', c.url)
        self.check_no_content(c)
        self.assertEqual({'name': 'alice'}, data)

    def test_nullable_with_non_none_default_overridden_with_none(self):
        @endpoint
        def func(name: str | None = 'default') -> None: ...
        c, data = make_url_test(func, None)
        self.assertEqual('/func', c.url)
        self.check_no_content(c)
        self.assertEqual({}, data)


if __name__ == '__main__':
    unittest.main()
