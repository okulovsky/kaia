import unittest
from dataclasses import dataclass
from foundation_kaia.marshalling import CallModel, endpoint, parse_json


@dataclass
class Data:
    value: int

class TestJsonBody(unittest.TestCase):
    def helper(self, f, *args):
        call_model = CallModel.Factory.test(f)(*args)
        c = call_model.content
        self.assertEqual({}, c.raw_values)
        parsed = {}
        parse_json(parsed, c.json_values, call_model.endpoint_model.params.json_params)
        return c, parsed

    def test_dataclass_serialized_to_json(self):
        @endpoint
        def func(p: Data) -> None: ...
        c, kw = self.helper(func, Data(1))
        self.assertEqual({'p': {'value': 1}}, c.json_values)
        self.assertEqual("/func", c.url)
        self.assertEqual({'p': Data(value=1)}, kw)

    def test_multiple_json_params(self):
        @endpoint
        def func(p: Data, q: Data) -> None: ...
        c, kw = self.helper(func, Data(2), Data(3))
        self.assertEqual({'p': {'value': 2}, 'q': {'value': 3}}, c.json_values)
        self.assertEqual("/func", c.url)
        self.assertEqual({'p': Data(value=2), 'q': Data(value=3)}, kw)

    def test_primitive_path_plus_json_body(self):
        @endpoint
        def func(a: int, b: int | None, p: Data) -> None: ...
        c, kw = self.helper(func, 5, 6, Data(99))
        self.assertIn('/5?b=6', c.url)
        self.assertEqual({'p': {'value': 99}}, c.json_values)
        self.assertEqual({'p': Data(value=99)}, kw)

    def test_force_json_params_primitive(self):
        @endpoint(force_json_params=True, verify_abstract=False)
        def func(a: int, b: str) -> None:
            pass
        c, kw = self.helper(func, 5, 'hello')
        self.assertEqual({'a': 5, 'b': 'hello'}, c.json_values)
        self.assertEqual('/func', c.url)
        self.assertEqual({'a': 5, 'b': 'hello'}, kw)

    def test_force_json_params_nullable(self):
        @endpoint(force_json_params=True, verify_abstract=False)
        def func(a: int, b: int | None) -> None:
            pass
        c, kw = self.helper(func, 1, None)
        self.assertEqual({'a': 1, 'b': None}, c.json_values)
        self.assertEqual('/func', c.url)

    def test_json_parameter_default(self):
        @endpoint
        def func(p: Data, q: Data = Data(3)) -> None: ...
        c, kw = self.helper(func, Data(1))
        self.assertEqual({'p': {'value': 1}}, c.json_values)
        self.assertEqual("/func", c.url)
        self.assertEqual({'p': Data(value=1)}, kw)

        c, kw = self.helper(func, Data(1), Data(2))
        self.assertEqual({'p': {'value': 1}, 'q': {'value': 2}}, c.json_values)
        self.assertEqual("/func", c.url)
        self.assertEqual({'p': Data(value=1), 'q': Data(value=2)}, kw)


if __name__ == '__main__':
    unittest.main()
