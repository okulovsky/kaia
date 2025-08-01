import unittest
from enum import Enum
from dataclasses import dataclass
from avatar.server.serialization import to_json, from_json

class Color(Enum):
    RED = 1
    GREEN = 2

class CustomClass:
    def __init__(self, x):
        self.x = x

@dataclass
class SimpleDC:
    x: int
    y: str

class TestDeserializationErrors(unittest.TestCase):
    def test_wrong_primitive_type_error(self):
        with self.assertRaises(ValueError) as cm:
            from_json("abc", int, "/foo/")
        msg = str(cm.exception)
        self.assertIn("Deserialization error at path /foo/: type <class 'int'> is expected", msg)
        self.assertTrue(msg.endswith("but the value was abc"))

    def test_enum_wrong_type_error(self):
        with self.assertRaises(ValueError) as cm:
            from_json(123, Color, "/e/")
        msg = str(cm.exception)
        self.assertIn("Deserialization error at path /e/: enum <enum 'Color'> is expected", msg)
        self.assertTrue(msg.endswith("but the value was 123"))

    def test_enum_invalid_member_error(self):
        with self.assertRaises(ValueError) as cm:
            from_json("BLUE", Color, "/e/")
        msg = str(cm.exception)
        self.assertIn("Deserialization error at path /e/: value BLUE is not a member of enum <enum 'Color'>", msg)

    def test_tuple_wrong_type_error(self):
        with self.assertRaises(ValueError) as cm:
            from_json("notalist", tuple, "/t/")
        msg = str(cm.exception)
        self.assertIn("Deserialization error at path /t/: tuple is expected, but the value is not list", msg)

    def test_non_dataclass_dict_error(self):
        with self.assertRaises(ValueError) as cm:
            from_json({"a": 1}, CustomClass, "/c/")
        msg = str(cm.exception)
        self.assertIn("CustomClass'>, but was dictionary", msg)

    def test_dataclass_nested_field_error(self):
        bad = {"x": "bad_int", "y": "ok"}
        with self.assertRaises(ValueError) as cm:
            from_json(bad, SimpleDC, "/")
        msg = str(cm.exception)
        self.assertIn("Deserialization error at path /x/: type <class 'int'> is expected, but the value was bad_int", msg)

