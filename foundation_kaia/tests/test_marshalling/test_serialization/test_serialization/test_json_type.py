import unittest
from dataclasses import dataclass
from datetime import datetime

from foundation_kaia.marshalling.serialization import Serializer, SerializationContext, JSON


def _ctx():
    return SerializationContext(path=[], allow_base64=True)


def _ser(tp):
    return Serializer.parse(tp)


class TestJSONDirectly(unittest.TestCase):
    """Serializer with annotation=JSON passes JSON values through unchanged."""

    def setUp(self):
        self.s = _ser(JSON)

    def _roundtrip(self, value):
        ctx = _ctx()
        serialized = self.s.to_json(value, ctx)
        restored = self.s.from_json(serialized, ctx)
        self.assertEqual(value, restored)
        return serialized

    def test_none(self):
        self.assertIsNone(self._roundtrip(None))

    def test_bool(self):
        self._roundtrip(True)
        self._roundtrip(False)

    def test_int(self):
        self._roundtrip(42)

    def test_float(self):
        self._roundtrip(3.14)

    def test_str(self):
        self._roundtrip("hello")

    def test_list(self):
        self._roundtrip([1, "two", None, True, [3, 4]])

    def test_dict(self):
        self._roundtrip({"a": 1, "b": [2, 3], "c": {"nested": True}})

    def test_non_json_raises(self):
        with self.assertRaises(TypeError):
            self.s.to_json(datetime(2025, 1, 1), _ctx())

    def test_object_raises(self):
        with self.assertRaises(TypeError):
            self.s.to_json(object(), _ctx())

    def test_dict_with_non_string_key_raises(self):
        with self.assertRaises(TypeError):
            self.s.to_json({1: "value"}, _ctx())

    def test_list_with_non_json_element_raises(self):
        with self.assertRaises(TypeError):
            self.s.to_json([1, datetime(2025, 1, 1)], _ctx())


class TestDictStrJSON(unittest.TestCase):
    """dict[str, JSON] works: values can be any JSON type."""

    def setUp(self):
        self.s = _ser(dict[str, JSON])

    def test_roundtrip(self):
        value = {"x": 1, "y": [True, None], "z": {"nested": "ok"}}
        ctx = _ctx()
        self.assertEqual(value, self.s.from_json(self.s.to_json(value, ctx), ctx))

    def test_non_json_value_raises(self):
        with self.assertRaises(TypeError):
            self.s.to_json({"key": datetime(2025, 1, 1)}, _ctx())


class TestDataclassWithJSONField(unittest.TestCase):
    """A dataclass with a JSON-annotated field serializes correctly."""

    def setUp(self):
        @dataclass
        class Config:
            name: str
            data: JSON

        self.Config = Config
        self.s = _ser(Config)

    def test_roundtrip_with_dict(self):
        obj = self.Config(name="cfg", data={"key": [1, 2, 3]})
        ctx = _ctx()
        restored = self.s.from_json(self.s.to_json(obj, ctx), ctx)
        self.assertEqual(obj, restored)

    def test_roundtrip_with_list(self):
        obj = self.Config(name="cfg", data=[1, "two", None])
        ctx = _ctx()
        restored = self.s.from_json(self.s.to_json(obj, ctx), ctx)
        self.assertEqual(obj, restored)

    def test_roundtrip_with_none(self):
        obj = self.Config(name="cfg", data=None)
        ctx = _ctx()
        restored = self.s.from_json(self.s.to_json(obj, ctx), ctx)
        self.assertEqual(obj, restored)

    def test_non_json_field_raises(self):
        obj = self.Config(name="cfg", data=datetime(2025, 1, 1))
        with self.assertRaises(TypeError):
            self.s.to_json(obj, _ctx())
