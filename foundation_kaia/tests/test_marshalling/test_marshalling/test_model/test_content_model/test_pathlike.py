import unittest
from pathlib import Path
from foundation_kaia.marshalling import endpoint, EndpointModel
from foundation_kaia.tests.test_marshalling.test_marshalling.test_model.test_content_model.tool import make_url_test


class TestIsPathlike(unittest.TestCase):

    def test_pathlike_param_appears_in_url_path(self):
        @endpoint(is_pathlike='path')
        def func(path: str) -> None: ...
        c, data = make_url_test(func, 'folder/sub')
        self.assertEqual('/func/folder/sub', c.url)
        self.assertEqual({}, c.json)

    def test_pathlike_str_value_preserved_in_url(self):
        @endpoint(is_pathlike='path')
        def func(path: str) -> None: ...
        c, data = make_url_test(func, 'a/b/c')
        self.assertEqual('/func/a/b/c', c.url)

    def test_pathlike_path_object_serialized_to_string(self):
        @endpoint(is_pathlike='path')
        def func(path: str | Path) -> None: ...
        c, _ = make_url_test(func, Path('some/folder'))
        self.assertEqual('/func/some/folder', c.url)

    def test_pathlike_is_last_path_segment(self):
        @endpoint(is_pathlike='path')
        def func(id: int, path: str) -> None: ...
        c, _ = make_url_test(func, 42, 'docs/readme')
        self.assertEqual('/func/42/docs/readme', c.url)

    def test_pathlike_empty_string(self):
        @endpoint(is_pathlike='path')
        def func(path: str) -> None: ...
        c, _ = make_url_test(func, '')
        self.assertEqual('/func/', c.url)

    def test_pathlike_stores_pathlike_param(self):
        @endpoint(is_pathlike='path')
        def func(path: str) -> None: ...
        model = EndpointModel.parse(func)
        self.assertIsNotNone(model.params.pathlike_param)
        self.assertEqual('path', model.params.pathlike_param.name)

    def test_without_pathlike_pathlike_param_is_none(self):
        @endpoint
        def func(name: str) -> None: ...
        model = EndpointModel.parse(func)
        self.assertIsNone(model.params.pathlike_param)

    def test_pathlike_overrides_force_json_params(self):
        @endpoint(is_pathlike='path', force_json_params=True, verify_abstract=False)
        def func(path: str) -> None:
            pass
        c, _ = make_url_test(func, 'some/path')
        self.assertEqual('/func/some/path', c.url)
        self.assertNotIn('path', c.json)

    def test_pathlike_other_params_still_use_force_json(self):
        @endpoint(is_pathlike='path', force_json_params=True, verify_abstract=False)
        def func(path: str, value: int) -> None:
            pass
        c, _ = make_url_test(func, 'some/path', 42)
        self.assertEqual('/func/some/path', c.url)
        self.assertIn('value', c.json)
        self.assertEqual(42, c.json['value'])

    def test_pathlike_query_params_still_work(self):
        @endpoint(is_pathlike='path')
        def func(path: str, prefix: str | None) -> None: ...
        c, _ = make_url_test(func, 'folder', 'img_')
        self.assertEqual('/func/folder?prefix=img_', c.url)

    def test_pathlike_none_in_query_omitted(self):
        @endpoint(is_pathlike='path')
        def func(path: str, prefix: str | None) -> None: ...
        c, _ = make_url_test(func, 'folder', None)
        self.assertEqual('/func/folder', c.url)

    def test_pathlike_non_str_path_annotation_raises(self):
        with self.assertRaises(ValueError) as ctx:
            @endpoint(is_pathlike='path')
            def func(path: int) -> None: ...
            EndpointModel.parse(func)
        self.assertIn('str or Path', str(ctx.exception))

    def test_pathlike_dataclass_annotation_raises(self):
        from dataclasses import dataclass

        @dataclass
        class Data:
            value: int

        with self.assertRaises(ValueError) as ctx:
            @endpoint(is_pathlike='path')
            def func(path: Data) -> None: ...
            EndpointModel.parse(func)
        self.assertIn('str or Path', str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
