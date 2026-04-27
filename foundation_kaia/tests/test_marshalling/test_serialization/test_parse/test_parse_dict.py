import unittest
from typing import Optional, Union, Any
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

from foundation_kaia.marshalling.serialization import (
    Serializer, IntHandler, StringHandler, DataclassHandler, NoneHandler,
    ListHandler, DictHandler, EnumHandler,
)


class Color(Enum):
    RED = 'red'
    GREEN = 'green'


@dataclass
class Point:
    x: float
    y: float


@dataclass
class Label:
    name: str
    value: int


class TestParseDict(unittest.TestCase):

    def test_dict_str_int(self):
        result = Serializer.parse(dict[str, int])
        self.assertEqual(len(result.handlers), 1)
        desc = result.handlers[0]
        self.assertIsInstance(desc, DictHandler)
        self.assertIs(desc.python_type, dict)
        self.assertEqual(len(desc.key_serializer.handlers), 1)
        self.assertIsInstance(desc.key_serializer.handlers[0], StringHandler)
        self.assertEqual(len(desc.value_serializer.handlers), 1)
        self.assertIsInstance(desc.value_serializer.handlers[0], IntHandler)

    def test_dict_int_str(self):
        result = Serializer.parse(dict[int, str])
        desc = result.handlers[0]
        self.assertIsInstance(desc, DictHandler)
        self.assertIsInstance(desc.key_serializer.handlers[0], IntHandler)
        self.assertIsInstance(desc.value_serializer.handlers[0], StringHandler)

    def test_dict_enum_key(self):
        result = Serializer.parse(dict[Color, int])
        desc = result.handlers[0]
        self.assertIsInstance(desc, DictHandler)
        self.assertIsInstance(desc.key_serializer.handlers[0], EnumHandler)
        self.assertIs(desc.key_serializer.handlers[0].python_type, Color)

    def test_dict_str_list_value(self):
        result = Serializer.parse(dict[str, list[int]])
        desc = result.handlers[0]
        self.assertIsInstance(desc, DictHandler)
        self.assertIsInstance(desc.key_serializer.handlers[0], StringHandler)
        self.assertIsInstance(desc.value_serializer.handlers[0], ListHandler)
        self.assertIsInstance(desc.value_serializer.handlers[0].element_serializer.handlers[0], IntHandler)

    def test_dict_str_optional_value(self):
        result = Serializer.parse(dict[str, int | None])
        desc = result.handlers[0]
        self.assertIsInstance(desc, DictHandler)
        self.assertEqual(len(desc.value_serializer.handlers), 2)
        types = {type(h) for h in desc.value_serializer.handlers}
        self.assertEqual(types, {IntHandler, NoneHandler})

    def test_optional_dict(self):
        result = Serializer.parse(Optional[dict[str, int]])
        self.assertEqual(len(result.handlers), 2)
        types = {type(h) for h in result.handlers}
        self.assertIn(NoneHandler, types)
        self.assertIn(DictHandler, types)
