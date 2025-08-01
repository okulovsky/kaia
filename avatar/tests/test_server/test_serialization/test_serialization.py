import unittest
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from avatar.server.serialization import to_json, from_json

class Color(Enum):
    RED = 1
    GREEN = 2

@dataclass
class DC:
    a: int
    b: str = "hi"
    c: float = 3.14
    d: datetime = datetime(2000, 1, 1)

class CustomClass:
    def __init__(self, x):
        self.x = x
    def __eq__(self, other):
        return isinstance(other, CustomClass) and self.x == other.x

class TestSerializeDeserialize(unittest.TestCase):
    def test_primitives_serialize_passthrough(self):
        for v in (None, True, False, 0, 42, 3.14, "text"):
            with self.subTest(v=v):
                self.assertEqual(v, to_json(v, type(v)))

    def test_primitives_deserialize_passthrough(self):
        cases = [
            (None, None, None),
            (True, True, bool),
            (123, 123, int),
            (2.71, 2.71, float),
            ("s", "s", str),
        ]
        for raw, expected, t in cases:
            with self.subTest(raw=raw, t=t):
                self.assertEqual(expected, from_json(raw, t))

    def test_datetime_serialize_to_iso(self):
        dt = datetime(2025, 7, 25, 12, 0, 0)
        s = to_json(dt, datetime)
        self.assertIsInstance(s, str)
        self.assertEqual("2025-07-25T12:00:00", s)

    def test_datetime_deserialize_returns_string(self):
        iso = "2025-07-25T12:00:00"
        self.assertEqual(iso, from_json(iso, datetime))

    def test_enum_serialize_and_deserialize(self):
        self.assertEqual("GREEN", to_json(Color.GREEN, Color))
        self.assertEqual(Color.RED, from_json("RED", Color))

    def test_tuple_serialize_and_deserialize(self):
        tup = (1, "a", 3.0)
        self.assertEqual([1, "a", 3.0], to_json(tup, tuple))
        self.assertEqual((4, 5, 6), from_json([4, 5, 6], tuple))

    def test_list_and_dict_passthrough(self):
        data = {"x": [1, 2, {"y": 3}]}
        s = to_json(data, dict)
        self.assertEqual(data, s)
        r = from_json(s, dict)
        self.assertEqual(data, r)

    def test_dataclass_serialization(self):
        inst = DC(a=1, b="bye", c=2.5, d=datetime(2021, 1, 1))
        s = to_json(inst, DC)
        self.assertIsInstance(s, dict)
        # a, b, c are primitives → unchanged
        self.assertEqual(1, s["a"])
        self.assertEqual("bye", s["b"])
        self.assertEqual(2.5, s["c"])
        # d is datetime → isoformat
        self.assertEqual("2021-01-01T00:00:00", s["d"])

    def test_dataclass_deserialization(self):
        data = {
            "a": 7,
            "b": "hello",
            "c": 9.81,
            "d": "2022-02-02T00:00:00"
        }
        r = from_json(data, DC)
        self.assertIsInstance(r, DC)
        self.assertEqual(7, r.a)
        self.assertEqual("hello", r.b)
        self.assertEqual(9.81, r.c)
        # datetime remains string
        self.assertEqual("2022-02-02T00:00:00", r.d)

    def test_custom_class_fallback_jsonpickle(self):
        obj = CustomClass({"foo": "bar"})
        s = to_json(obj, None)
        self.assertIsInstance(s, dict)
        self.assertIn("py/object", s)
        r = from_json(s, None)
        self.assertIsInstance(r, CustomClass)
        self.assertEqual(obj, r)

    def test_deserialize_plain_dict_for_none_type(self):
        plain = {"a": 1, "b": 2}
        self.assertEqual(plain, from_json(plain, None))

    def test_error_on_unexpected_dict_for_scalar(self):
        with self.assertRaises(ValueError):
            from_json({"x": 1}, int)

if __name__ == "__main__":
    unittest.main()
