import unittest
from typing import Any
from enum import Enum
from datetime import datetime

from foundation_kaia.marshalling_2.serialization import (
    Serializer, IntHandler, FloatHandler, StringHandler, BoolHandler,
    EnumHandler, DateTimeHandler, NoneHandler, UnsupportedHandler,
)


class Color(Enum):
    RED = 'red'
    GREEN = 'green'


class Priority(Enum):
    LOW = 1
    HIGH = 3


class TestParsePrimitives(unittest.TestCase):

    def test_int(self):
        result = Serializer.parse(int)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], IntHandler)
        self.assertIs(result.handlers[0].python_type, int)

    def test_float(self):
        result = Serializer.parse(float)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], FloatHandler)
        self.assertIs(result.handlers[0].python_type, float)

    def test_str(self):
        result = Serializer.parse(str)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], StringHandler)
        self.assertIs(result.handlers[0].python_type, str)

    def test_bool(self):
        result = Serializer.parse(bool)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], BoolHandler)
        self.assertIs(result.handlers[0].python_type, bool)

    def test_none_type(self):
        result = Serializer.parse(type(None))
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], NoneHandler)
        self.assertIs(result.handlers[0].python_type, type(None))

    def test_datetime(self):
        result = Serializer.parse(datetime)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], DateTimeHandler)
        self.assertIs(result.handlers[0].python_type, datetime)

    def test_string_enum(self):
        result = Serializer.parse(Color)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], EnumHandler)
        self.assertIs(result.handlers[0].python_type, Color)

    def test_int_enum(self):
        result = Serializer.parse(Priority)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], EnumHandler)
        self.assertIs(result.handlers[0].python_type, Priority)

    def test_any(self):
        result = Serializer.parse(Any)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], UnsupportedHandler)

    def test_unrecognized_type(self):
        result = Serializer.parse(object)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], UnsupportedHandler)

    def test_custom_class_not_dataclass(self):
        class Foo:
            pass
        result = Serializer.parse(Foo)
        self.assertEqual(len(result.handlers), 1)
        self.assertIsInstance(result.handlers[0], UnsupportedHandler)


if __name__ == '__main__':
    unittest.main()
