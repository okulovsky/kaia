import unittest
from typing import Optional, Union
from enum import Enum
from datetime import datetime

from foundation_kaia.marshalling.serialization import (
    Serializer, IntHandler, FloatHandler, StringHandler, BoolHandler,
    EnumHandler, DateTimeHandler, NoneHandler,
)


class Color(Enum):
    RED = 'red'
    GREEN = 'green'


class TestParseUnions(unittest.TestCase):

    def test_union_two_types(self):
        result = Serializer.parse(Union[int, str])
        self.assertEqual(len(result.handlers), 2)
        self.assertIsInstance(result.handlers[0], IntHandler)
        self.assertIsInstance(result.handlers[1], StringHandler)

    def test_union_three_types(self):
        result = Serializer.parse(Union[int, str, float])
        self.assertEqual(len(result.handlers), 3)
        self.assertIsInstance(result.handlers[0], IntHandler)
        self.assertIsInstance(result.handlers[1], StringHandler)
        self.assertIsInstance(result.handlers[2], FloatHandler)

    def test_pipe_syntax(self):
        result = Serializer.parse(int | str)
        self.assertEqual(len(result.handlers), 2)
        self.assertIsInstance(result.handlers[0], IntHandler)
        self.assertIsInstance(result.handlers[1], StringHandler)

    def test_pipe_three_types(self):
        result = Serializer.parse(int | str | bool)
        self.assertEqual(len(result.handlers), 3)
        self.assertIsInstance(result.handlers[0], IntHandler)
        self.assertIsInstance(result.handlers[1], StringHandler)
        self.assertIsInstance(result.handlers[2], BoolHandler)

    def test_union_with_enum(self):
        result = Serializer.parse(Union[str, Color])
        self.assertEqual(len(result.handlers), 2)
        self.assertIsInstance(result.handlers[0], StringHandler)
        self.assertIsInstance(result.handlers[1], EnumHandler)
        self.assertIs(result.handlers[1].python_type, Color)


class TestParseNullables(unittest.TestCase):

    def test_optional_int(self):
        result = Serializer.parse(Optional[int])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {IntHandler, NoneHandler})

    def test_optional_str(self):
        result = Serializer.parse(Optional[str])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {StringHandler, NoneHandler})

    def test_optional_enum(self):
        result = Serializer.parse(Optional[Color])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {EnumHandler, NoneHandler})

    def test_pipe_none(self):
        result = Serializer.parse(int | None)
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {IntHandler, NoneHandler})

    def test_union_int_str_none(self):
        result = Serializer.parse(int | str | None)
        self.assertEqual(len(result.handlers), 3)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {IntHandler, StringHandler, NoneHandler})

    def test_optional_float(self):
        result = Serializer.parse(Optional[float])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {FloatHandler, NoneHandler})

    def test_optional_datetime(self):
        result = Serializer.parse(Optional[datetime])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertEqual(types, {DateTimeHandler, NoneHandler})


if __name__ == '__main__':
    unittest.main()
